TRIM_APPNAME="${TRIM_APPNAME:-EasyTier-Lite}"
RUST_BACKTRACE=1 && /var/apps/${TRIM_APPNAME}/target/bin/easytier-cli connector
RUST_BACKTRACE=1 && /var/apps/${TRIM_APPNAME}/target/bin/easytier-cli peer
