#!/bin/bash
rm -i log.db

sqlite3 log.db < log_ddl.sql

