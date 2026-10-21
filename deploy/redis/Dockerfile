FROM redis:7.4-alpine
COPY --chmod=0555 start.sh /usr/local/bin/foodify-redis
USER redis
CMD ["/usr/local/bin/foodify-redis"]
