-- resistivity_block_iter[#].dat 2nd block
create table cellGroupResistivity(
    cellId integer primary key,
    resistivity real,
    resistivityLower real,
    resistivityUpper real,
    n real,
    fixFlag integer
);
-- resistivity_block_iter[#].dat 1st block
create table elementCellGroup(
    elementId integer primary key,
    cellId integer
);
-- -- resistivity_block_iter[#].dat 3rd block
-- create table YZplane(
--     elementId integer primary key,
--     planeIndex integer
-- );
-- mesh.dat
create table elementNode(
    elementId integer primary key,
    adj0ElemId integer,
    adj1ElemId integer,
    adj2ElemId integer,
    adj3ElemId integer,
    node0Id integer,
    node1Id integer,
    node2Id integer,
    node3Id integer
);
-- mesh.dat
create table nodePos(
    nodeId integer primary key,
    posX real,
    posY real,
    posZ real
);

-- view
create table elementNodePosWithResistivity(
    elementId integer primary key,
    cellId integer,
    resistivity real,
    node0posx real, 
    node0posy real, 
    node0posz real, 
    node1posx real, 
    node1posy real, 
    node1posz real, 
    node2posx real, 
    node2posy real, 
    node2posz real, 
    node3posx real, 
    node3posy real, 
    node3posz real 
);
