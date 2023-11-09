drop type if exists "sex" cascade;

drop table if exists chanel_member cascade;
drop table if exists feedback cascade;
drop table if exists favorite_category cascade;
drop table if exists meeting_category cascade;
drop table if exists category cascade;
drop table if exists meeting_member cascade;
drop table if exists meeting cascade;
drop table if exists chanel cascade;
drop table if exists passport_rf cascade;
drop table if exists passport cascade;
drop table if exists car cascade;
drop table if exists person cascade;
drop table if exists country cascade;

drop function if exists inc_members_cnt_trigger_func();
drop function if exists dec_members_cnt_trigger_func();
drop function if exists calc_meeting_rating_trigger_func();
drop function if exists calc_chanel_rating_func();
