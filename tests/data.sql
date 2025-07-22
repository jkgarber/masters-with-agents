INSERT INTO users (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 1),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO master_items (creator_id, name)
VALUES
	(2, 'item name 1'),
	(2, 'item name 2'),
	(2, 'item name 3'),
	(3, 'item name 4'),
	(3, 'item name 5'),
	(3, 'item name 6');

INSERT INTO master_details (creator_id, name, description)
VALUES
	(2, 'detail name 1', 'detail description 1'),
	(2, 'detail name 2', 'detail description 2'),
	(2, 'detail name 3', 'detail description 3'),
	(3, 'detail name 4', 'detail description 4'),
	(3, 'detail name 5', 'detail description 5'),
	(3, 'detail name 6', 'detail description 6');

INSERT INTO master_item_detail_relations (master_item_id, master_detail_id, content)
VALUES
	(1, 1, 'relation content 1'),
	(1, 2, 'relation content 2'),
	(2, 1, 'relation content 3'),
	(2, 2, 'relation content 4'),
	(3, 3, 'relation content 5'),
	(4, 4, 'relation content 6'),
	(4, 5, 'relation content 7'),
	(5, 4, 'relation content 8'),
	(5, 5, 'relation content 9'),
	(6, 6, 'relation content 10');

INSERT INTO masters (creator_id, master_type, name, description)
VALUES
	(2, 'list', 'master name 1', 'master description 1'),
	(2, 'list', 'master name 2', 'master description 2'),
	(3, 'list', 'master name 3', 'master description 3'),
	(3, 'list', 'master name 4', 'master description 4'),
	(2, 'agent', 'master name 5', 'master description 5'),
	(2, 'agent', 'master name 6', 'master description 6'),
	(3, 'agent', 'master name 7', 'master description 7');

INSERT INTO master_item_relations (master_id, master_item_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3),
	(3, 4),
	(3, 5),
	(4, 6);

INSERT INTO master_detail_relations (master_id, master_detail_id)
VALUES
	(1, 1),
	(1, 2),
	(2, 3),
	(3, 4),
	(3, 5),
	(4, 6);

INSERT INTO master_agents (creator_id, model, role, instructions, vendor)
VALUES
	(2, 'gpt-4o-mini', 'Testing Agent 1', 'Reply with one word: "Working" 1.', 'openai'),
	(2, 'claude-3-5-haiku-latest', 'Testing Agent 2', 'Reply with one word: "Working" 2.', 'anthropic'),
	(3, 'gemini-1.5-flash-8b', 'Testing Agent 3', 'Reply with one word: "Working". 3', 'google');

INSERT INTO master_agent_relations (master_id, master_agent_id)
VALUES
	(5, 1),
	(6, 2),
	(7, 3);
