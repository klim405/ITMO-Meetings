insert into person (referrer_id, username, first_name, patronymic, last_name, other_names,
                    sex, age, telephone, email, password_hash)
    values
        (null, 'user1', 'elison', null, 'argent', null,
         'female', 18, '+79995552233', 'f@mail.ru', 'pbkdf2:sha512:600000$CLXiyoIKoAQEYRdh1OlLLfIFpvK7Ywye$1e9f85e93bd9addcd7438f90ef2ec9fb9c6c801c171c4ff0aad9c45e48c268928af6b47fda9a78d7c99fbf29d0a6d0acd1cb4eb89b2d331b29ef4554c0257b43'),
        (null, 'user2', 'scot', null, 'maccall', null,
         'male', 19, '+79995552244', 'ghjk@mail.ru', 'pbkdf2:sha512:600000$yUdPbzaO6YkcYghot3m8EtgQm2XJ6qzZ$1c1cf892dd5f1f25a5df8aea1a4a19941fa4399093fe11a262cd794e448db9bc3cff6b601870b6431c5db55993995632a2bb7c5b59099b1397fe44b28df3373d'),
        (null, 'user3', 'styles', null, 'stilinsky', null,
         'male', 18, '+79995559933', 'stilinsky@mail.ru', 'pbkdf2:sha512:600000$syIOmnlgZtcd8cWepl69R83lYFGowP0o$3e40a2fc6eb55a5087dac98ce7ed57ac9179a7b1e2dc675095a7cf6b729c4c8afbf019ed761f1c3a511df10b7a3e192d8791bf25b1a73b7a05f7fd32aabf00ac');

insert into chanel (name)
    values
           ('elison chanel'),
           ('scot chanel'),
           ('styles chanel');

insert into chanel_member (chanel_id, user_id, permissions)
    values
        (1, 1, 0),
        (2, 2, 0),
        (3, 3, 0),
        (2, 1, 0),
        (2, 3, 0);

delete from chanel_member where chanel_id = 2 and user_id = 3;

