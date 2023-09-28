#!/bin/bash

TIMEOUT=600  # 10 минут

LAST_LOG_TIME=$(journalctl -u hotel_synchronize.service --since "10 minutes ago" -o short-iso | tail -n 1 | cut -d" " -f1)
CURRENT_TIME=$(date -Iseconds)

DIFF=$(date -u -d "$CURRENT_TIME" +%s)
LAST=$(date -u -d "$LAST_LOG_TIME" +%s)

if (( DIFF - LAST > TIMEOUT )); then
    systemctl restart hotel_synchronize.service
fi
