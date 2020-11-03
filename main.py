#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# FoxyGFW - Generate GFWList rules file for FoxyProxy extension
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
#
# This file is part of FoxyGFW.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from base64 import b64decode
from configparser import RawConfigParser
from json import load, dump
from re import sub
from requests import get
from typing import Union

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    filename="log",
    filemode="a"
)
logger = logging.getLogger(__name__)

# Read data from config.ini

# [proxy]
enabled: Union[bool, str] = ""
hostname: str = ""
port: str = ""

# [custom]
url: str = ""

try:
    config = RawConfigParser()
    config.read("config.ini")

    # [proxy]
    enabled = config["proxy"].get("enabled", enabled)
    enabled = eval(enabled)
    hostname = config["proxy"].get("hostname", hostname)
    port = config["proxy"].get("port", port)

    # [custom]
    url = config["custom"].get("url", url)
except Exception as e:
    logger.warning(f"Read data from config.ini error: {e}", exc_info=True)

# Check
if (enabled not in {False, True}
        or hostname == ""
        or port == ""
        or url == ""):
    logger.critical("No proper settings")
    raise SystemExit("No proper settings")

# Set proxy
if enabled:
    proxies = {
        "http": f"socks5://{hostname}:{port}",
        "https": f"socks5://{hostname}:{port}"
    }
else:
    proxies = None

# Read base.json

with open("base.json") as f:
    base = load(f)

base["whitePatterns"] = []


def get_dict(rule: str) -> (int, dict):
    # Get pattern dict
    result = (0, {})

    try:
        protocol = 1
        white = 1

        # White rule
        if rule.startswith("@@"):
            rule = rule[2:]
        else:
            white = 0

        # Get protocol
        if rule.startswith("|http://"):
            protocol = 2
            rule = sub("^\\|http://", "|", rule)
        elif rule.startswith("|https://"):
            protocol = 4
            rule = sub("^\\|https://", "||", rule)

        # Get match type
        if rule.startswith("||"):
            rule = f"*.{rule[2:]}"
        elif rule.startswith("|"):
            rule = rule[1:]

        # Format the rule
        rule = rule.split("/")[0]

        if "." not in rule:
            rule = f"*{rule}*"

        the_dict = {
            "title": rule,
            "pattern": rule,
            "type": 1,
            "protocols": protocol,
            "active": True
        }

        result = (white, the_dict)
    except Exception as ee:
        print(f"[ERROR] Get dict error: {e}")
        logger.warning(f"Get dict error: {ee}", exc_info=True)

    return result


def main() -> bool:
    result = False

    try:
        copyright_text = ("FoxyProxy, Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>\n"
                          "Licensed under the terms of the GNU General Public License v3 or later (GPLv3+)\n" +
                          "-" * 24)
        print(copyright_text)

        result = get(url, proxies=proxies)

        if not result or not result.content:
            return False

        text = b64decode(result.content)
        text = text.decode("utf-8")

        if not text:
            return False

        print("[INFO] Got the GFWList!")
        print("[INFO] Processing...")

        rules = list(filter(None, text.split("\n")))

        for rule in rules:
            if rule.startswith("[AutoProxy"):
                continue

            if rule.startswith("!"):
                continue

            if rule.startswith("/") and rule.endswith("/"):
                continue

            white, the_dict = get_dict(rule)

            if not the_dict:
                continue

            if white:
                base["blackPatterns"].append(the_dict)
            else:
                base["whitePatterns"].append(the_dict)

        print("[INFO] Saving the output file...")

        with open("output.json", "w") as ff:
            dump(base, ff, indent=4)

        print("[INFO] Succeeded!")
        print("[INFO] Please check the file: output.json")

        result = True
    except Exception as ee:
        print(f"[ERROR] Main function error: {e}")
        logger.warning(f"Error: {ee}", exc_info=True)

    return result


if __name__ == "__main__":
    main()
