DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS masters;
DROP TABLE IF EXISTS master_items;
DROP TABLE IF EXISTS master_details;
DROP TABLE IF EXISTS master_item_detail_relations;
DROP TABLE IF EXISTS master_item_relations;
DROP TABLE IF EXISTS master_detail_relations;
DROP TABLE IF EXISTS master_agents;
DROP TABLE IF EXISTS master_agent_relations;

CREATE TABLE users (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username TEXT UNIQUE NOT NULL,
	password TEXT NOT NULL
);

CREATE TABLE masters (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	master_type TEXT NOT NULL,
	name TEXT NOT NULL,
	description TEXT,
	FOREIGN KEY (creator_id) REFERENCES users (id)
);

CREATE TABLE master_items (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	name TEXT NOT NULL,
	FOREIGN KEY (creator_id) REFERENCES users (id)
);

CREATE TABLE master_details (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	name TEXT NOT NULL,
	description TEXT,
	FOREIGN KEY (creator_id) REFERENCES users (id)
);

CREATE TABLE master_item_detail_relations (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	master_item_id INTEGER NOT NULL,
	master_detail_id INTEGER NOT NULL,
	content TEXT,
	FOREIGN KEY (master_item_id) REFERENCES master_items (id)
	FOREIGN KEY (master_detail_id) REFERENCES master_details (id)
);

CREATE TABLE master_item_relations (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	master_id INTEGER NOT NULL,
	master_item_id INTEGER NOT NULL,
	FOREIGN KEY (master_id) REFERENCES masters (id),
	FOREIGN KEY (master_item_id) REFERENCES master_items (id)
);

CREATE TABLE master_detail_relations (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	master_id INTEGER NOT NULL,
	master_detail_id INTEGER NOT NULL,
	FOREIGN KEY (master_id) REFERENCES masters (id),
	FOREIGN KEY (master_detail_id) REFERENCES master_details (id)
);

CREATE TABLE master_agents (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	model TEXT NOT NULL,
	role TEXT NOT NULL,
	instructions TEXT NOT NULL,
	vendor TEXT NOT NULL,
	FOREIGN KEY (creator_id) REFERENCES users (id)
);

CREATE TABLE master_agent_relations (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	master_id INTEGER NOT NULL,
	master_agent_id INTEGER NOT NULL,
	FOREIGN KEY (master_id) REFERENCES masters (id),
	FOREIGN KEY (master_agent_id) REFERENCES agents (id)
);
