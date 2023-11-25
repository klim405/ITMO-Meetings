create type gender as enum (
    'male',
    'female'
);

create table person (
    user_id serial primary key,
    referrer_id int references person (user_id),
    username varchar(20) unique,
    firstname varchar(20) not null,
    patronymic varchar(20),
    surname varchar(20) not null,
    other_names varchar(256),
    gender gender not null,
    date_of_birth date not null,
    telephone varchar(64) unique not null,
    email varchar(320) unique not null,
    password_hash char(182) not null,
    confidentiality integer not null
        default 418,
    is_staff bool not null
        default false,
    is_active bool not null
        default true
);

create index person_pk on person (user_id);
create index person_username on person (username);
create index person_telephone on person (telephone);
create index person_email on person (email);


create table channel (
    channel_id serial primary key,
    name varchar(100) not null,
    description text,
    members_cnt integer not null
        check ( members_cnt >= 0 )
        default 0,
    rating float
        check ( rating >= 0 AND rating <= 5)
        default null,
    is_personal bool not null
        default false,
    is_public bool not null
        default true,
    is_active bool not null
        default true
);

create index channel_pk on channel (channel_id);
create index channel_name on channel (name);
create index channel_rating on channel (rating);


create table channel_member (
    channel_id int references channel (channel_id)
        on delete CASCADE
        on update CASCADE,
    user_id int references person (user_id)
        on delete CASCADE
        on update CASCADE,
    date_of_join timestamp with time zone
        default CURRENT_TIMESTAMP,
    permissions integer not null
        default 0,
    is_owner bool not null
        default false,
    notify_about_meeting bool not null
        default false
);

create index channel_member_pk on channel_member (channel_id, user_id);
create index channel_member_permissions on channel_member (permissions);

-- Триггеры и функции для подсчета подписчиков
create function inc_members_cnt_trigger_func() returns trigger as $$
    begin
        update channel
            set members_cnt = (select members_cnt from channel
                               where channel_id = new.channel_id) + 1
            where channel.channel_id = new.channel_id;
        return null;
    end;
    $$ language plpgsql;

create trigger channel_member_insert after insert on channel_member
    for each row execute procedure inc_members_cnt_trigger_func();

create function dec_members_cnt_trigger_func() returns trigger as $$
    begin
        update channel
            set members_cnt = (select members_cnt from channel
                               where channel_id = old.channel_id) - 1
            where channel.channel_id = old.channel_id;
        return null;
    end;
    $$ language plpgsql;

create trigger channel_member_delete after delete on channel_member
    for each row execute procedure dec_members_cnt_trigger_func();

create table meeting (
    meeting_id serial primary key,
    channel_id int references channel (channel_id),
    title varchar(256) not null,
    description text,
    start_datetime timestamp with time zone not null
        check ( start_datetime > CURRENT_TIMESTAMP ),
    duration_in_minutes int,
    address varchar(512) not null,
    capacity int not null
        check ( capacity > 0 )
        default 4,
    price int not null
        check ( price >= 0 )
        default 0,
    minimum_age smallint not null
        check ( minimum_age >= 0 )
        default 0,
    maximum_age smallint not null
        check ( maximum_age >= 0 )
        default 150,
    only_for_itmo_students bool not null
        default false,
    only_for_russians bool not null
        default false,
    rating float,
    is_public bool not null
        default true
);

create index meeting_pk on meeting (meeting_id);
create index meeting_channel_id on meeting (channel_id);
create index meeting_title on meeting (title);
create index meeting_start_time on meeting (start_datetime);
create index meeting_address on meeting (address);
create index meeting_capacity on meeting (capacity);
create index meeting_price on meeting (price);
create index meeting_minimum_age on meeting (minimum_age);
create index meeting_maximum_age on meeting (maximum_age);
create index meeting_for_itmo_students on meeting (only_for_itmo_students);
create index meeting_for_russians on meeting (only_for_russians);


create table feedback (
    user_id int references person(user_id)
        on delete CASCADE
        on update CASCADE,
    meeting_id int references meeting(meeting_id)
        on delete CASCADE
        on update CASCADE,
    rate smallint not null
        check ( rate >= 0 AND rate <= 5),
    constraint
        one_feedback_per_user unique (user_id, meeting_id)
);

create index feedback_pk on feedback (user_id, meeting_id);

-- Процедура и триггеры для вычисление рейтинга события (meeting.py) на основе отзывов
create function calc_meeting_rating_trigger_func() returns trigger as $$
    begin
        if (TG_OP = 'DELETE') then
            update meeting
                set rating = (select avg(rate) from feedback where meeting_id = old.meeting_id)
                where meeting_id = old.meeting_id;
        else
            update meeting
                set rating = (select avg(rate) from feedback where meeting_id = new.meeting_id)
                where meeting_id = new.meeting_id;
        end if;
        return null;
    end;
    $$ language plpgsql;

create trigger feedback_insert after insert or update or delete on feedback
    for each row execute procedure calc_meeting_rating_trigger_func();


-- Процедура и триггеры для вычисление рейтинга канала (channel) на основе отзывов
create function calc_channel_rating_func() returns trigger as $$
    begin
        if (TG_OP = 'DELETE') then
            update channel
                set rating = (select avg(rating) from meeting where channel_id = new.channel_id)
                where channel_id = new.channel_id;
        else
            update channel
                set rating = (select avg(rating) from meeting where channel_id = new.channel_id)
                where channel_id = new.channel_id;
        end if;
        return null;
    end;
    $$ language plpgsql;

create trigger meeting_insert after insert or update or delete on meeting
    for each row execute procedure calc_channel_rating_func();


create table category (
    category_id serial primary key,
    name varchar(20) not null
--  todo: icon
);

create index category_pk on category (category_id);


create table favorite_category (
    user_id int references person (user_id)
        on delete CASCADE
        on update CASCADE,
    category_id int references category (category_id)
        on delete CASCADE
        on update CASCADE,
    constraint
        favorite_categories_pk primary key (user_id, category_id)
);

create index favorite_category_pk on favorite_category (user_id, category_id);


create table meeting_category (
    meeting_id int references meeting (meeting_id)
        on delete CASCADE
        on update CASCADE,
    category_id int references category (category_id)
        on delete CASCADE
        on update CASCADE,
    constraint
        meeting_category_pk primary key (meeting_id, category_id)
);

create index meeting_category_pk_idx on meeting_category (meeting_id, category_id);


create table meeting_member (
    meeting_id int references meeting(meeting_id) 
        on delete CASCADE
        on update CASCADE,
    user_id int references person(user_id) 
        on delete CASCADE
        on update CASCADE,
    date_of_join timestamp with time zone not null
        default CURRENT_TIMESTAMP,
    constraint
        meeting_member_pk unique (meeting_id, user_id)
);

create index meeting_member_pk_idx on meeting_member (meeting_id, user_id);


create table passport_rf (
    number bigint primary key,
    user_id int references person(user_id)
        on delete CASCADE
        on update CASCADE,
    code int not null,
    issue_date date not null
        check (issue_date > CURRENT_DATE ),
    birth_date date not null
        check (birth_date > CURRENT_DATE ),
    who_give text not null
);

create index passport_rf_user_id on passport_rf (user_id);


create table country (
    country_id serial primary key,
    title varchar(60) not null
);

create index country_pk on country(country_id);


create table passport (
    number varchar(10) not null,
    country_id int references country(country_id)
        on delete CASCADE
        on update CASCADE,
    user_id int references person(user_id)
        on delete CASCADE
        on update CASCADE,
    issue_date date not null
        check (issue_date > CURRENT_DATE ),
    expire_date date not null
        check (birth_date > CURRENT_DATE ),
    birth_date date not null
        check (birth_date > CURRENT_DATE ),
    birth_place text not null,
    constraint
        passport_pk primary key (number, country_id)
);

create index passport_user_id on passport (user_id);


create table car (
    number varchar(10) primary key,
    user_id int references person (user_id)
        on delete CASCADE
        on update CASCADE,
    country_id int references country(country_id)
        on delete CASCADE
        on update CASCADE
);


create or replace function create_personal_channel(in ch_name varchar(100), out integer) as $$
    insert into channel (name, is_personal) values (ch_name, true) returning channel_id;
$$ language sql;


create function insert_person_trigger_func() returns trigger as $$
    declare
        last_id integer;
    begin
        last_id = create_personal_channel(trim(to_char(new.user_id, '9999999999')));
        insert into channel_member (channel_id, user_id, permissions, is_owner) values
            (last_id, new.user_id, 32767, true);
        return null;
    end;
    $$ language plpgsql;

create trigger f after insert on person
    for each row execute procedure insert_person_trigger_func()