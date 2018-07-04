Steps to use Redis on a Dev Workstation (MAC):
==============================================
See this article as base reference: https://gist.github.com/tomysmile/1b8a321e7c58499ef9f9441b2faa0aa8

type below:

```
brew update
brew install redis
```

To have launchd start redis now and restart at login:
```
brew services start redis
```

Or, if you don't want/need a background service you can just run:

```
redis-server /usr/local/etc/redis.conf
```

Test if Redis server is running.

```
redis-cli ping
```
If it replies “PONG”, then it’s good to go!

Location of Redis configuration file.

```
/usr/local/etc/redis.conf
```

Uninstall Redis and its files.

```
brew uninstall redis
rm ~/Library/LaunchAgents/homebrew.mxcl.redis.plist
```
