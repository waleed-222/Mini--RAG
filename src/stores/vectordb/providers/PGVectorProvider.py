from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import (DistanceMethodEnums,PgvectorDistanceMethodEnums,
                             PgVectorTableSchemeEnums,PgVectorIndexTypeEnums)

import  logging
from typing import List
from models.db_schemes import RetrivedDocument
from sqlalchemy.sql import text as sql_text
import json

class PGVectorProvider(VectorDBInterface):
    
    def __init__(self,db_client,default_vector_size:int=786,
                 distance_method:str=None):
        self.db_client=db_client
        self.default_vector_size=default_vector_size
        self.distance_method=distance_method
        self.pgvector_table_prefix= PgVectorTableSchemeEnums._PREFIX.value
        
        self.logger = logging.getLogger('uvicorn')
        self.default_index_name = lambda collection_name:f"{collection_name}_vector_idx"
        

            
    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(
                    sql_text(
                        "CREATE EXTENSION IF NOT EXISTS vector"
                    )
                )
            await session.commit()
    
    async def disconnect(self):
            pass
        
    async def is_collection_existed(self,collection_name:str) -> bool:
        record=None
        async with self.db_client() as session:
                 async with session.begin():
                     list_table = sql_text("SELECT * FROM pg_tables WHERE tablename = :collection_name")
                     results = await session.execute(list_table,{"collection_name":collection_name})
                     record = results.scalar_one_or_none()
        return record
    
    async def list_all_collections(self)-> List:
        records=[]
        async with self.db_client() as session:
              async with session.begin():
                list_tbl=sql_text("SELECT tablename FROM pg_table WHERE tablename LIKE :prefix")
                results = await session.execute(list_tbl,{"prefix":self.pgvector_table_prefix})
                records = results.scalars().all()
        
        return records
    
    async def get_collection_info(self,collection_name:str)-> dict:
        async with self.db_client() as session:
              async with session.begin():
                    table_info_sql=sql_text('''
                     SELECT schemname, tablename, tableowner, tablespace, hasindex
                     FROM pg_tables 
                     WHERE tablename = :collection_name
                     ''')
                    count_sql=sql_text(f"SELECT COUNT(*) FROM :collection_name")
                    table_info = await session.execute(table_info_sql,{"collectio_name"})
                    table_count = await session.execute(count_sql,{"collectio_name"})
                    
                    table_info = table_info.fetchone()
                    
                    if not table_info:
                        return None
                    
                    return {
                        "table_info":table_info,
                        "table_count":table_count
                    }
                    
                    
    async def delete_collection(self,collection_name:str):

        async with self.db_client() as session:
              async with session.begin():
                    self.logger.info(f"Deleting collection:{collection_name} ")
                    delete_sql=sql_text("DROP TABLE IF EXISTS :collection_name")
                    await session.execute(delete_sql,{"collection_name":collection_name})
                    await session.commit()
        return True
    
    
    async def create_collection(self,collection_name:str,embedding_size:int,do_rest: bool=False):

        if do_rest:
            _=await self.delete_collection(collection_name=collection_name)
            
        is_collection_existed = await self.is_collection_existed(collection_name)
        
        if not self.is_collection_existed:
            self.logger.info(f"Creating collection: {collection_name}")
            async with self.db_client() as session:
              async with session.begin():
                    create_sql = sql_text(f'CREATE TABLE {collection_name}('
                                            f'{PgVectorTableSchemeEnums.ID.value} bigserial PRIMARY KEY,'
                                            f'{PgVectorTableSchemeEnums.TEXT.value} text, '
                                            f'{PgVectorTableSchemeEnums.VECTOR.value} vector({embedding_size}),'
                                            f'{PgVectorTableSchemeEnums.METADATA.value} jsonb DEFAULT \'{{}}\','
                                            f'{PgVectorTableSchemeEnums.CHUNK_ID.value} integer,'
                                            f'FOREIGN KEY({PgVectorTableSchemeEnums.CHUNK_ID.value}) REFERENCE chunks(chunk_id)'
                                        ')')
                    await session.execute(create_sql)
                    await session.commit()
            return True
        
        return False
    
    async def is_index_existed(self,collection_name:str)-> bool:
        index_name =self.default_index_name(collection_name=collection_name)
        async with self.db_client() as session:
            async with session.begin():
                    check_sql=sql_text(
                        
                    )
    
    async def instert_one(self,collection_name:str,text:str,vector:list,
                    metadata:dict=None,
                    record_id:str=None):
        is_collection_existed =await self.is_collection_existed(collection_name=collection_name)
        
        if not is_collection_existed:
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")        
            return False
        
                
        if not record_id:
            self.logger.error(f"Can not insert new record without chunk_id: {collection_name}")        
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                insert_sql = sql_text(
                    f"INSERT INTO {collection_name}"
                    f"({PgVectorTableSchemeEnums.TEXT.value}, {PgVectorTableSchemeEnums.VECTOR.value},{PgVectorTableSchemeEnums.METADATA.value}, {PgVectorTableSchemeEnums.CHUNK_ID.value})"
                    "VALUES (:text,:vector,:metadata,:chunk_id)"
                )
                await session.execute(insert_sql,{
                    'text':text,
                    'vector':"["+",".join([str(v) for v in vector])+"]",
                    'metadata':metadata,
                    'chunk_id':record_id
                })
                await session.commit()
        return True
    
    async def insert_many(self,collection_name:str, texts:list,
                    vectors:list, metadata: list =None,
                    record_ids: list=None, batch_size:int=50
                    ):
        is_collection_existed =await self.is_collection_existed(collection_name=collection_name)
        
        if not is_collection_existed:
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")        
            return False
        
        if len(vectors) != len(record_ids):
            self.logger.error(f"Invalid data items for collection: {collection_name}")
            return False
        
        if  not metadata or len(metadata)==0:
            metadata = [None]*len(texts)
        
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0,len(texts),batch_size):
                    batch_text= texts[i:i+batch_size]
                    batch_vectors= vectors[i:i+batch_size]
                    batch_metadata = metadata[i:i+batch_size]
                    batch_record_ids = record_ids[i:i+batch_size]
                    
                    values=[]
                    
                    for _text, _vector, _metadata, _record_id in zip(batch_text,batch_vectors,batch_metadata,batch_record_ids):
                        values.append(
                            {
                                'text':_text,
                                'vector':"["+",".join([str(v) for v in _vector])+"]",
                                'metadata':_metadata,
                                'chunk_id':_record_id
                                
                            }
                        )
                    batch_insert_sql = sql_text(
                        f"INSERT INTO {collection_name}"
                    f"({PgVectorTableSchemeEnums.TEXT.value},"
                    f"{PgVectorTableSchemeEnums.VECTOR.value},"
                    f"{PgVectorTableSchemeEnums.METADATA.value},"
                    f"{PgVectorTableSchemeEnums.CHUNK_ID.value})"
                    "VALUES (:text,:vector,:metadata,:chunk_id)"
                    )
                    await session.execute(batch_insert_sql,values)
                    await session.commit()
        return True
    
    async def search_by_vector(self, collection_name:str, vector:list, limit:int=5):
         
        is_collection_existed =await self.is_collection_existed(collection_name=collection_name)
 
        if not is_collection_existed:
            self.logger.error(f"Can not search for records to non-existed collection: {collection_name}")        
            return False
        
        
        
        vector = "["+",".join([str(v) for v in vector])+"]",
        
        async with self.db_client() as session:
            async with session.begin():
                search_sql = sql_text(
                    f"SELECT {PgVectorTableSchemeEnums.TEXT.value} as text, "
                    f"(1- {PgVectorTableSchemeEnums.VECTOR.value} <=> :vector) as score"
                    f"FROM {collection_name}"
                    f"ORDER BY score DESC"
                    f"LIMIT {limit}"
                )
                
                result = await session.execute(search_sql,{"vector":vector})
                records = result.fetchall()
                
                return [
                    
                    RetrivedDocument(
                        text=record.text,
                        score=record.score
                    )
                    for record in records
                ]
                                                


