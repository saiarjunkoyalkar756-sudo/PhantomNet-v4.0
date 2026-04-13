# PhantomNet Agent Installation on Termux

This guide provides instructions for installing the PhantomNet agent on Termux.

## Prerequisites

-   Termux application installed on your Android device.
-   `python` and `pip` installed in Termux (`pkg install python`).

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-repo/phantomnet.git
    cd phantomnet/phantomnet_agent
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Agent:**
    You can run the agent directly for testing:
    ```bash
    python main.py --config config/agent.yml
    ```

## Autorun on Boot (Optional)

To make the agent run automatically on boot, you can use the `Termux:Boot` app.

1.  **Install Termux:Boot:**
    Install the `Termux:Boot` app from F-Droid or the Google Play Store.

2.  **Create Boot Script:**
    Create a new directory `~/.termux/boot/` if it doesn't exist.
    ```bash
    mkdir -p ~/.termux/boot
    ```

3.  **Create the Start Script:**
    Create a new file `~/.termux/boot/start-phantomnet-agent` with the following content:
    ```bash
    #!/data/data/com.termux/files/usr/bin/sh
    cd /data/data/com.termux/files/home/phantomnet/phantomnet_agent
    python main.py --config config/agent.yml > agent_output.log 2>&1 &
    ```

4.  **Make the Script Executable:**
    ```bash
    chmod +x ~/.termux/boot/start-phantomnet-agent
    ```

The agent will now start automatically whenever you open the Termux:Boot app or reboot your device.
