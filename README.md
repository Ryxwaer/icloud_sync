# icloud_sync
script to sync Logseq folder between iCloud and my linux PC


## docker

### build

`docker build -t ryxwaer/icloud_sync:latest .`

### run

```
docker run -it \
    -v $HOME/icloud:/usr/src/app/Documents/icloud \
    -v icloud_sync_cookies:/usr/src/app/cookies \
    ryxwaer/icloud_sync:latest
```
