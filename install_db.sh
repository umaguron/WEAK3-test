#!/bin/bash
ls log.db &>/dev/null && rm -i log.db 

sqlite3 log.db < log_ddl.sql

ls log.db &>/dev/null || echo failed to create log.db
ls log.db &>/dev/null && echo new log.db created

