insert into person (referrer_id, username, first_name, patronymic, last_name, other_names,
                    sex, age, telephone, email, password, pwd_salt)
    values
        (null, 'user1', 'elison', null, 'argent', null,
         'female', 18, '+79995552233', 'f@mail.ru', 'ad8dd4f85dd89852eef4b4bf54e364b0516f3b080f3c6d37320b79b9f0f75ddf324f0266009ae1bcab9caf599fb5f5521f64f1a968a4eef4883ea92bfc5770d0', '6aef2f1506b4b6ea5fc2eea21e790d40'),
        (null, 'user2', 'scot', null, 'maccall', null,
         'male', 19, '+79995552244', 'ghjk@mail.ru', '214db9b66c0461577b6b733818aa4f3a7ae8922d979a90fe841185d9c32815051cb66781a52f0d033655ade76c439efb709aef53b9638518595e22f9e80fff73', '26e5c5965825fee6116acb592ddae7b0'),
        (null, 'user3', 'styles', null, 'stilinsky', null,
         'male', 18, '+79995559933', 'stilinsky@mail.ru', '9517b40ea705c7f763d52e05b092af81785bc886082df7f5b34e9037c3a8032f52dac98fb9fde0a40aee6e867c589e0271627a7ed88047616ca94a2a27a1c5bf', 'd20592b08457a85c3b1e03ed7dd28841');

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

