-- список каналов и их владельцев
select person.username, channel.name
    from person
    left outer join channel_member
        on person.user_id = channel_member.user_id and type_of_access = 'owner'
    left outer join channel
        on channel.channel_id = channel_member.channel_id;