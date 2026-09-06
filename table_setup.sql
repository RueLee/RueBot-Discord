CREATE TABLE IF NOT EXISTS guild (
    guild_id BIGINT UNSIGNED NOT NULL,
    guild_name VARCHAR(255) NOT NULL,
    date_created DATE NOT NULL,
    PRIMARY KEY (guild_id)
);

CREATE TABLE IF NOT EXISTS guild_user (
    user_id BIGINT UNSIGNED NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    join_date DATE NOT NULL,
    PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS level (
    guild_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    level INT NOT NULL,
    role VARCHAR(255),
    exp FLOAT NOT NULL,
    exp_level_up INT NOT NULL,
    PRIMARY KEY (guild_id, user_id),
    FOREIGN KEY (guild_id) REFERENCES guild(guild_id),
    FOREIGN KEY (user_id) REFERENCES guild_user(user_id)
);

CREATE TABLE IF NOT EXISTS user_mute (
    guild_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    mute_count INT UNSIGNED NOT NULL,
    scheduled_decrement DATETIME NOT NULL,
    prev_scheduled_decrement DATETIME,          -- Backup if staff has unmuted a player and needed to roll back
    PRIMARY KEY (guild_id, user_id),
    FOREIGN KEY (guild_id) REFERENCES guild(guild_id),
    FOREIGN KEY (user_id) REFERENCES guild_user(user_id)
);