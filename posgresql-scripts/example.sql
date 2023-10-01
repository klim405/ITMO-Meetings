-- список каналов и их владельцев
select person.username, chanel.name
    from person
    left outer join chanel_member
        on person.user_id = chanel_member.user_id and type_of_access = 'owner'
    left outer join chanel
        on chanel.chanel_id = chanel_member.chanel_id;