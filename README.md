# LINE Badminton Queue Bot

This project is a **LINE bot** that allows users to **join queues** for different badminton courts, managing **court reservations**, player rotations, and **permission-controlled administrative actions**. The bot is built using **FastAPI** with **SQLAlchemy** for data handling, and it uses **MySQL** for persistent storage.

## Features

* **Queue Management**: Users can join and check the queue for badminton courts, including multiple courts with automatic player rotation.
* **Permission Control**: Only users with proper permissions (admins) can execute certain commands like `START`, `END`, and `CLEAR`.
* **Bot State**: The bot can be **ON** or **OFF** per group, controlled by admin users. Commands are only functional when the bot is **ON**.
* **Admin Actions**: Admins can manage the bot's state, clear all queues, and more.

## Installation

### Prerequisites

1. **Python 3.10+**: Make sure you're using Python 3.10 or higher.
2. **MySQL 8**: Install and configure a MySQL database for persistence.
3. **LINE Developer Account**: You need to create a **LINE messaging API** channel and get the `CHANNEL_ACCESS_TOKEN` and `CHANNEL_SECRET`.

### Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/christang0316/Line_Bot_Court_Enrollment_System.git
   cd Line_Bot_Court_Enrollment_System
   ```

2. **Set up the environment**:

   * Create a `.env` file and add the following variables:

     ```
     CHANNEL_ACCESS_TOKEN=your_channel_access_token
     CHANNEL_SECRET=your_channel_secret
     DATABASE_URL=mysql+pymysql://user:password@localhost:3306/line_queue?charset=utf8mb4
     ```

   * Replace `your_channel_access_token`, `your_channel_secret`, and `user:password` with your actual credentials from Line Developer.

3. **Set up the database**:

   * Ensure you have a MySQL database set up and the necessary tables created. Run the following SQL to create the tables:

     ```sql
     CREATE DATABASE IF NOT EXISTS `line_queue`;
     USE `line_queue`;

     -- Create group_bot_state table (stores bot state for each group)
     CREATE TABLE IF NOT EXISTS `group_bot_state` (
       `group_id` VARCHAR(64) NOT NULL,
       `bot_state` TINYINT(1) NOT NULL DEFAULT 0,
       PRIMARY KEY (`group_id`)
     );

     -- Create queue_entry table (stores queue entries for each court)
     CREATE TABLE IF NOT EXISTS `queue_entry` (
       `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
       `court` ENUM('A','B','C','D') NOT NULL,
       `user_id` VARCHAR(64) NOT NULL,
       `user_name` VARCHAR(128) NOT NULL,
       `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       PRIMARY KEY (`id`),
       UNIQUE KEY `uq_queue_user_per_court` (`court`, `user_id`),
       KEY `idx_court_id` (`court`, `id`),
       KEY `idx_user_id` (`user_id`)
     );

     -- Admin permissions table (stores user permissions for admin actions)
     CREATE TABLE IF NOT EXISTS `admin_permission` (
       `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
       `user_id` VARCHAR(64) NOT NULL,
       `group_id` VARCHAR(64) NOT NULL,
       `can_start_bot` TINYINT(1) NOT NULL DEFAULT 0,
       `can_end_bot` TINYINT(1) NOT NULL DEFAULT 0,
       `can_clear` TINYINT(1) NOT NULL DEFAULT 0,
       PRIMARY KEY (`id`),
       UNIQUE KEY `uq_admin_user_group` (`user_id`, `group_id`),
       KEY `idx_group_id` (`group_id`)
     );
     ```

4. **Run the application**:

   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

   This will start the bot, and you should now be able to send messages to the bot in a group chat.

## Usage

1. **Invite the bot to a group**: Add the bot to a group in LINE.
2. **Basic Commands**:

   * `A+1`, `B+1`, `C+1`, `D+1`: Enroll the user in the respective court.
   * `A NEXT`, `B NEXT`, `C NEXT`, `D NEXT`: Move to the next player in the court’s queue.
   * `CHECK`: Check if you are enrolled in any queue.
   * `STATUS`: Check the current status of all queues.
   * `CANCEL`: Cancel your enrollment in the queue.
   * `SHOW USER ID`: Display your user ID.
3. **Admin Commands** (for authorized users only):

   * `START`: Start the bot (make sure the bot is **ON** for the group).
   * `END`: Stop the bot (make sure the bot is **ON** for the group).
   * `CLEAR`: Clear all queues for all courts (requires admin permission).
4. **Bot State**: Admins can toggle the bot's **ON/OFF** state for the group using the `START` and `END` commands. Non-admin users will be notified if the bot is off.

## Future Work

1. **Dynamic Court Numbers**: Currently, the system supports only four courts (`A`, `B`, `C`, `D`). A future enhancement could involve **dynamically deciding the number of courts** (e.g., based on user input or configuration).

2. **Multiple Group Support**: Right now, the bot only supports one group (one queue system). In the future, we could expand this to support **multiple groups** with their own queue systems. This would require updating the `queue_entry` table to store multiple group chat queues.

3. **User-Friendly Features**: Further improvements to the user experience, such as:

   * Customizing quick reply buttons based on the available courts.
   * Automatically notifying users when it's their turn to play.

4. **Optimization**: Improve performance for larger user bases, e.g., caching frequently accessed data or using a more scalable database solution.

---

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests. Make sure to follow the coding style and add tests for new features.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

