create table person (
    user_id serial primary key,
    referrer_id int references person (user_id),
    username varchar(20) unique,
    first_name varchar(20) not null,
    patronymic varchar(20),
    last_name varchar(20) not null,
    other_names varchar(256),
    age smallint not null,
    telephone varchar(16) not null,
    email varchar(320) not null,
    password varchar(256) not null,
    pwd_salt char(6) not null,
    is_staff bool not null
        default false,
    is_active bool not null
        default true
);

create table meeting (
    meeting_id serial primary key,
    organizer_id int references person (user_id) not null,
    title varchar(256)                           not null,
    description text,
    start_datetime timestamp with time zone      not null
        check ( start_datetime > CURRENT_TIME ),
    duration interval,
    address varchar(512)                         not null,
    capacity int                                 not null
        check ( capacity > 0 )
        default 4,
    price int                                    not null
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
--     rating
);

create table category (
    category_id serial primary key,
    title varchar(20) not null
--     icon
);

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

create table meeting_category (
    meeting_id int references user_meeting (meeting_id)
        on delete CASCADE
        on update CASCADE,
    category_id int references category (category_id)
        on delete CASCADE
        on update CASCADE,
    constraint
        favorite_categories_pk primary key (meeting_id, category_id)
);

create table feedback (
    feedback_id bigserial primary key,
    user_id int references person(user_id) not null,
    meeting_id int references user_meeting(meeting_id) not null,
    rate smallint not null
        check ( rate >= 0 AND rate <= 5),
    constraint
        one_feedback_per_user unique (user_id, meeting_id)
);