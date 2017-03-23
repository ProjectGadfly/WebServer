# Insert minimum necessary values
INSERT INTO call_scripts (title, content, unique_id, expiration_date)
VALUES ("My Script", "Make some calls!", "2763134", CURDATE() + INTERVAL 6 MONTH);

# View all data in table
# SELECT * FROM call_scripts;



# Insert several paragraphs of text in the content field
INSERT INTO call_scripts (title, content, unique_id, expiration_date)
VALUES ("Pragraphs", "On the lush alien world of Pandora live the Na'vi, beings who appear primitive but are highly evolved.
  Because the planet's environment is poisonous, human/Na'vi hybrids, called Avatars, must link to human minds to allow for free movement on Pandora.
   Avatar: an electronic image that represents and is manipulated by a computer user in a virtual space (as in a computer game or an online shopping site) and that interacts with other objects in the space.",
   "2000", CURDATE() + INTERVAL 6 MONTH);
