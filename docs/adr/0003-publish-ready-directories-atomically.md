# Publish only ready directories

Writers create a temporary sibling directory, write payload and manifest there, and rename it into the key location only after success. Readers therefore never interpret a partially written entry as a cache hit.
