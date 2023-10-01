create table auth_token (
    token uuid primary key,
    refresh_token uuid unique not null,
    expire_time timestamp with time zone not null
        default CURRENT_TIMESTAMP + interval '1m',
    user_id int not null references person (user_id)
        on update CASCADE
        on delete CASCADE
);