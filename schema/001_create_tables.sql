\c autoinvest


create table scheduled_orders (
    ticker       varchar(64)                not null,
    currency     varchar(10)                not null,
    amount       double precision           not null,
    execute_at   timestamp with time zone   not null,

    primary key (ticker, execute_at)
);
create index on scheduled_orders (execute_at);


create table orders (
    ticker         varchar(64)                not null,
    amount         double precision           not null,
    currency       varchar(10)                not null,
    created_at     timestamp with time zone   not null
);


create table leftovers (
    ticker   varchar(64)        primary key,
    amount   double precision   not null default 0
);

create table state (
    key     varchar(64)   primary key,
    value   text          not null
);

create table metadata (
    key     varchar(64)   primary key,
    value   jsonb         not null
);

create table messages (
    text      text                       not null,
    sent_at   timestamp with time zone   not null
);
create index on messages (sent_at);