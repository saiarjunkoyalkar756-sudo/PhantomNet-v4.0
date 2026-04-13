### START SCRIPT
#!/data/data/com.termux/files/usr/bin/bash

set -e

PREFIX="/data/data/com.termux/files/usr"
NIX_ROOT="$PREFIX/nix"

echo "[*] Creating /data/data/com.termux/files/usr/nix directory..."
mkdir -p "$NIX_ROOT"

echo "[*] Extracting minimal Nix store structure..."
mkdir -p "$NIX_ROOT/store"

echo "[*] Creating required environment variables for Nix..."
cat <<EOF > $PREFIX/etc/profile.d/nix.sh
export NIX_CONF_DIR=$PREFIX/etc/nix
export NIX_ROOT=$PREFIX/nix
export NIX_PATH=nixpkgs=$PREFIX/nix/var/nix/profiles/per-user/$(whoami)/channels/nixpkgs
export PATH=\$PATH:$PREFIX/nix/var/nix/profiles/default/bin:$PREFIX/nix/bin
EOF

echo "[*] Creating Nix config directory..."
mkdir -p $PREFIX/etc/nix

echo "[*] Writing default Nix config..."
cat <<EOF > $PREFIX/etc/nix/nix.conf
sandbox = false
substituters = https://cache.nixos.org/
trusted-substituters = *
experimental-features = nix-command flakes
EOF

echo "[*] Bootstrapping minimal Nix environment..."
mkdir -p $PREFIX/nix/var/nix/profiles/default/bin

echo "[*] Downloading Nix binary tarball from official cache..."
curl -L https://nixos.org/releases/nix/nix-2.18.1/nix-2.18.1-aarch64-linux.tar.xz -o nix.tar.xz

echo "[*] Extracting Nix..."
tar -xJf nix.tar.xz -C $PREFIX/nix --strip-components=1

echo "[*] Setting up Nix daemonless mode..."
$PREFIX/nix/bin/nix-store --init

echo "[*] Installation complete!"
echo "Run: source $PREFIX/etc/profile.d/nix.sh"
echo "Then: nix-env --version"
### END SCRIPT
