-- Switch to the target database
USE okayii;

-- Create 'renders' table to store rendering job details
CREATE TABLE renders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    commander_id VARCHAR(255) NOT NULL,
    no_of_frames INT NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    status ENUM('rendering', 'rendered', 'failed') NOT NULL DEFAULT 'rendering',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
