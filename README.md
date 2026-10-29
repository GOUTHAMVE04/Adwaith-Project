# College Educational Management System (EduManage)
### Course: ECT423 Computer Networks Project

A centralized, multi-user **Client–Server Educational Management System** built with Python Flask and SQLite, demonstrating real-world Computer Networks and Web Architecture concepts.

---

## 1. Computer Network Concepts Demonstrated

| Network Concept | Implementation in this Project |
| :--- | :--- |
| **Client–Server Model** | Independent client terminals (web browsers) send HTTP requests; a single central Flask server processes requests and accesses the centralized database. |
| **Application Layer (HTTP)** | Uses standard `GET` and `POST` methods, headers, status codes (`200 OK`, `302 Found`, `403 Forbidden`, `404 Not Found`), and URL routing. |
| **Transport Layer (TCP/IP)** | The server listens on `0.0.0.0:5000`. TCP ensures reliable packet delivery, three-way handshaking, and byte-stream ordering. |
| **Stateful Sessions over Stateless HTTP** | Uses cryptographic cookies (`session`) to maintain user authentication across stateless HTTP requests. |
| **Centralized Database Storage** | Client terminals never directly access `college.db`. All queries are mediated by server-side parameterized SQL. |
| **Role-Based Access Control (RBAC)** | Strict server-side authorization decorators ensure users only access resources permitted by their role. |
| **Multi-Client Concurrency** | Multiple distinct devices (laptops, smartphones) on the same Wi-Fi network can simultaneously access the server. |

---

## 2. Default Login Credentials

For quick testing during viva and project demonstrations, the login portal includes **one-click demo buttons** to auto-fill these credentials:

| Role | Username | Password | Full Name / Description |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Principal / Admin Office |
| **Faculty 1** | `prof_smith` | `faculty123` | Dr. John Smith (Computer Networks) |
| **Faculty 2** | `prof_anjali` | `faculty123` | Prof. Anjali Nair (Wireless Comm.) |
| **Student 1** | `adwaith` | `student123` | Adwaith R. (S7 ECE, Roll: ECE2101) |
| **Student 2** | `sneha` | `student123` | Sneha Patel (S7 ECE, Roll: ECE2102) |
| **Student 3** | `rahul` | `student123` | Rahul Kumar (S7 ECE, Roll: ECE2103) |
| **Parent** | `parent_adwaith`| `parent123` | Mr. Radhakrishnan (Linked to Adwaith) |

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+ installed on your system.

### Step 1: Clone or Navigate to the Project Directory
```powershell
cd "c:\Users\HP\OneDrive\Desktop\Adwaith Project"
```

### Step 2: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts scripts, run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` or use `.\venv\Scripts\python app.py` directly).*

### Step 3: (Optional) Re-Seed Database
To reset the database to a fresh state with realistic test records at any time:
```powershell
python seed_data.py
```

### Step 4: Run the Central Server
```powershell
python app.py
```

### Step 5: Open in Your Browser
- Local Browser: [http://127.0.0.1:5000](http://127.0.0.1:5000) or [http://localhost:5000](http://localhost:5000)

---

## 4. How to Demonstrate Multi-Client LAN Access (Viva Demo)

To prove this is a genuine client–server network project, access the server from a smartphone or another laptop connected to the same Wi-Fi network:

### Step 1: Find the Host Server's Local IP Address
In PowerShell on the host PC:
```powershell
ipconfig
```
Look for **IPv4 Address** under your active Wi-Fi or Ethernet adapter (for example: `192.168.1.45`).

### Step 2: Allow Port 5000 in Windows Firewall (One-Time Setup)
Run this command in PowerShell as Administrator (or simply click "Allow" if Windows Defender prompts):
```powershell
New-NetFirewallRule -DisplayName "Flask EMS Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Step 3: Connect from Client Devices
1. Connect your smartphone or second laptop to the **same Wi-Fi network**.
2. Open the mobile browser (Chrome/Safari) and enter:
   ```text
   http://192.168.1.45:5000
   ```
   *(Replace `192.168.1.45` with your actual IP address).*
3. Log in as **Parent** on your phone and as **Faculty** on your PC.
4. Update attendance or marks on the PC, and instantly refresh the phone to show real-time centralized database synchronization!

---

## 5. Running the Automated Test Suite

A comprehensive test suite is included to verify all HTTP routes, authentication flows, and security constraints:

```powershell
python test_full_suite.py
```

### Expected Output:
```text
......
----------------------------------------------------------------------
Ran 6 tests in 0.570s

OK
```

---

## 6. Project Architecture Diagram

```text
+------------------------------------------------------------------------+
|                            CLIENT DEVICES                              |
|   +------------------+  +------------------+  +--------------------+   |
|   | Student Browser  |  | Faculty Browser  |  |   Parent Mobile    |   |
|   +--------+---------+  +--------+---------+  +---------+----------+   |
+------------|---------------------|----------------------|--------------+
             |                     |                      |
             +---------------------+----------------------+
                                   |
                         HTTP Requests (TCP/IP)
                               Port 5000
                                   |
                                   v
+------------------------------------------------------------------------+
|                         CENTRAL FLASK SERVER                           |
|  +------------------------------------------------------------------+  |
|  |  • WSGI HTTP Server                                              |  |
|  |  • Session & Cookie Authentication (PBKDF2 SHA-256)              |  |
|  |  • Role-Based Access Control (@role_required)                    |  |
|  |  • Jinja2 Template Engine (Bootstrap 5 Frontend)                |  |
|  +----------------------------------+-------------------------------+  |
+-------------------------------------|----------------------------------+
                                      |
                           SQL Queries / Cursors
                                      |
                                      v
+------------------------------------------------------------------------+
|                       CENTRAL SQLITE DATABASE                          |
|                             college.db                                 |
|  [users]      [students]     [faculty]    [parent_student] [subjects]  |
|  [attendance] [marks]        [timetable]  [notices]                    |
+------------------------------------------------------------------------+
```

