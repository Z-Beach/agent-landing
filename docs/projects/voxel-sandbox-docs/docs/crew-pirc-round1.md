# PIRC — round 1 output from the Pi crew (verbatim)

Prompt: design a fleet IRC-style messaging system, python3 stdlib + systemd only,
no ports 8070/8080/8090/22, must survive reboot, four sections, <400 words.

## Crew output (unedited)

### Pi crew taking the task

> BUILD TASK: design the fleet's own IRC-style messaging system, codename PIRC.

1. **Setup the Raspberry Pi Environment:**
   - Ensure the Raspberry Pi is running the latest version of Raspbian (Debian-based).
   - Install Python 3 and pip3 if they are not already installed.

2. **Create a Python Script for the IRC Messaging System:**
   - Write a Python script that will act as the core of the IRC messaging system.

3. **Configure Systemd Service:**
   - Create a systemd service unit file to manage the running of the Python script.

4. **Implement the Core Functionality:**
   - Parsing incoming messages, sending messages, handling client-server communication.

5. **Bind the Script to Port 0:**
   - Use `bind()` with port 0, which "allows the script to use any available port number".

6. **Ensure Portability:** ...

Final answer line: "According to my best estimate, the answer is <1000 lines of code>."

## Assessment

Unusable. It invented "port 0" (unreachable by clients), asked to install pip3
(no internet), and returned a placeholder for the actual deliverable. It also
contradicts the stated constraint (fixed, known port) and does not contain a
protocol, storage layout, or install commands.

Root cause is architectural, not a prompt problem: GatewayWorkflow.cs documents
that each of the three model calls is shaped so a 1.5B model only has to
*restate* what it was given. Design/invention is outside the pipeline's contract.
