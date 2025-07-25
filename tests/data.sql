INSERT INTO users (username, password, admin)
VALUES
  ("test", "pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f", 1),
  ("other", "pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79", 0);


INSERT INTO master_lists (creator_id, name, description)
VALUES
    (2, "master list name 1", "master list description 1"),
    (2, "master list name 2", "master list description 2");


INSERT INTO master_items (creator_id, name)
VALUES
	(2, "master item name 1"),
	(2, "master item name 2"),
	(2, "master item name 3");


INSERT INTO master_details (creator_id, name, description)
VALUES
	(2, "master detail name 1", "master detail description 1"),
	(2, "master detail name 2", "master detail description 2"),
	(2, "master detail name 3", "master detail description 3");


INSERT INTO master_item_detail_relations (master_item_id, master_detail_id, master_content)
VALUES
	(1, 1, "master relation content 1"),
	(1, 2, "master relation content 2"),
	(2, 1, "master relation content 3"),
	(2, 2, "master relation content 4"),
	(3, 3, "master relation content 5");


INSERT INTO master_list_item_relations (master_list_id, master_item_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3);


INSERT INTO master_list_detail_relations (master_list_id, master_detail_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3);


INSERT INTO master_agents (creator_id, name, description, model_id, role, instructions)
VALUES
	(2, "master agent name 1", "master agent description 1", 3, "master agent role 1", "Reply with one word: Working"),
	(2, "master agent name 2", "master agent description 2", 6, "master agent role 2", "Reply with one word: Working"),
	(2, "master agent name 3", "master agent description 3", 9, "master agent role 3", "Reply with one word: Working");


INSERT INTO agents (creator_id, name, description, model_id, role, instructions)
VALUES
	(2, "agent name 1", "agent description 1", 3, "agent role 1", "Reply with one word: Working"),
	(2, "agent name 2", "agent description 2", 6, "agent role 2", "Reply with one word: Working"),
	(3, "agent name 3", "agent description 3", 9, "agent role 3", "Reply with one word: Working");


INSERT INTO tethered_agents (creator_id, master_agent_id)
VALUES
    (2, 1),
    (2, 2),
    (3, 3);
