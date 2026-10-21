FROM mysql:8.4
COPY --chmod=0555 initialize-access.sh /docker-entrypoint-initdb.d/10-foodify-access.sh
CMD ["mysqld", "--character-set-server=utf8mb4", "--collation-server=utf8mb4_0900_ai_ci", "--default-time-zone=+00:00"]
