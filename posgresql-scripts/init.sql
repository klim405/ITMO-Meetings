create type "sex" as enum (
    'male',
    'female'
);

create table person (
    user_id serial primary key,
    referrer_id int references person (user_id),
    username varchar(20) unique,
    first_name varchar(20) not null,
    patronymic varchar(20),
    last_name varchar(20) not null,
    other_names varchar(256),
    sex sex not null,
    age smallint not null,
    telephone varchar(16) unique not null,
    email varchar(320) unique not null,
    password_hash char(182) not null,
    is_staff bool not null
        default false,
    is_active bool not null
        default true
);

create index person_pk on person (user_id);
create index person_username on person (username);
create index person_telephone on person (telephone);
create index person_email on person (email);


create table chanel (
    chanel_id serial primary key,
    name varchar(100) not null,
    description text,
    rating smallint
        check ( rating >= 0 AND rating <= 5)
        default null,
    is_personal bool not null
        default true,
    is_require_confirmation bool not null
        default false
);

create index chanel_pk on chanel (chanel_id);
create index chanel_name on chanel (name);
create index chanel_rating on chanel (rating);


create table chanel_member (
    chanel_id int references chanel (chanel_id)
        on delete CASCADE
        on update CASCADE,
    user_id int references person (user_id)
        on delete CASCADE
        on update CASCADE,
    date_of_join timestamp with time zone
        default CURRENT_TIMESTAMP,
    permissions integer not null
        default 0,
    notify_about_meeting bool not null
        default false
);

create index chanel_member_pk on chanel_member (chanel_id, user_id);
create index chanel_member_permissions on chanel_member (permissions);


create table meeting (
    meeting_id serial primary key,
    chanel_id int references chanel (chanel_id),
    title varchar(256) not null,
    description text,
    start_datetime timestamp with time zone not null
        check ( start_datetime > CURRENT_TIMESTAMP ),
    duration interval,
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
        default false
--  todo: rating
);

create index meeting_pk on meeting (meeting_id);
create index meeting_chanel_id on meeting (chanel_id);
create index meeting_title on meeting (title);
create index meeting_start_time on meeting (start_datetime);
create index meeting_address on meeting (address);
create index meeting_capacity on meeting (capacity);
create index meeting_price on meeting (price);
create index meeting_minimum_age on meeting (minimum_age);
create index meeting_maximum_age on meeting (maximum_age);
create index meeting_for_itmo_students on meeting (only_for_itmo_students);
create index meeting_for_russians on meeting (only_for_russians);


create table category (
    category_id serial primary key,
    title varchar(20) not null
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

create index meeting_category_pk on meeting_category (meeting_id, category_id);


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


create table meeting_member (
    meeting_id int references meeting(meeting_id) 
        on delete CASCADE
        on update CASCADE,
    user_id int references person(user_id) 
        on delete CASCADE
        on update CASCADE,
    date_of_join timestamp with time zone      not null
        check ( date_of_join > CURRENT_TIMESTAMP ),
    constraint
        meeting_member_pk unique (meeting_id, user_id)
);

create index meeting_member_pk on meeting_member (meeting_id, user_id);


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

create index car_user_id on car (user_id);
