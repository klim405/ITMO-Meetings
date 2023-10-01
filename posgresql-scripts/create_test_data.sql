insert into person (referrer_id, username, first_name, patronymic, last_name, other_names,
                    sex, age, telephone, email, password, pwd_salt)
    values
        (null, 'user1', 'elison', null, 'argent', null,
         'female', 18, '+79995552233', 'f@mail.ru', 'password', 'salt66'),
        (null, 'user2', 'scot', null, 'maccall', null,
         'male', 19, '+79995552244', 'ghjk@mail.ru', 'password', 'salt66'),
        (null, 'user3', 'styles', null, 'stilinsky', null,
         'male', 18, '+79995559933', 'stilinsky@mail.ru', 'password', 'salt66');

insert into chanel (name)
    values
           ('elison chanel'),
           ('scot chanel'),
           ('styles chanel');

insert into chanel_member (chanel_id, user_id, type_of_access)
    values
        (1, 1, 'owner'),
        (2, 2, 'owner'),
        (3, 3, 'owner'),
        (2, 1, 'member'),
        (2, 3, 'member');

