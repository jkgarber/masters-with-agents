DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS master_lists;
DROP TABLE IF EXISTS master_items;
DROP TABLE IF EXISTS master_details;
DROP TABLE IF EXISTS master_item_detail_relations;
DROP TABLE IF EXISTS master_list_item_relations;
DROP TABLE IF EXISTS master_list_detail_relations;
DROP TABLE IF EXISTS master_agents;

CREATE TABLE users (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username TEXT UNIQUE NOT NULL,
	password TEXT NOT NULL
);

CREATE TABLE master_lists (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
	master_content TEXT,
	FOREIGN KEY (master_item_id) REFERENCES master_items (id)
	FOREIGN KEY (master_detail_id) REFERENCES master_details (id)
);

CREATE TABLE master_list_item_relations (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	master_list_id INTEGER NOT NULL,
	master_item_id INTEGER NOT NULL,
	FOREIGN KEY (master_list_id) REFERENCES master_lists (id),
	FOREIGN KEY (master_item_id) REFERENCES master_items (id)
);

CREATE TABLE master_list_detail_relations (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	master_list_id INTEGER NOT NULL,
	master_detail_id INTEGER NOT NULL,
	FOREIGN KEY (master_list_id) REFERENCES master_lists (id),
	FOREIGN KEY (master_detail_id) REFERENCES master_details (id)
);

CREATE TABLE master_agents (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	name TEXT NOT NULL,
	description TEXT NOT NULL,
	model TEXT NOT NULL,
	role TEXT NOT NULL,
	instructions TEXT NOT NULL,
	provider TEXT NOT NULL,
	FOREIGN KEY (creator_id) REFERENCES users (id)
);
