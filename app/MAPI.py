import falcon
import falcon.asgi
import sqlalchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

#DB Setup
engine = sqlalchemy.create_engine("sqlite:///publicStreams.sqlite")
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class PublicStream(Base):
    __tablename__ = "publicstream"
    streamName = Column(String)
    streamIP = Column(String, primary_key=True)
    
Base.metadata.create_all(engine)

#Initialize falcon app instance
app = falcon.asgi.App()

class HealthCheck:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_TEXT
        resp.text = ('Operational!')
healthCheck = HealthCheck()
app.add_route('/status', healthCheck)        


#Endpoint for adding a new stream to the public stream database
class AddStream:
    async def on_post(self, req, resp):
        db = SessionLocal()
        try:
            
            data = await req.get_media()
            streamName = data.get("streamName")
            streamIP = data.get("streamIP")
            
            print(streamName)
            print(streamIP)
            
            newStreamItem = PublicStream(streamName = streamName, streamIP = streamIP)
            db.add(newStreamItem)
            db.commit()
            db.refresh(newStreamItem)
            
            resp.status = falcon.HTTP_200

        finally:
            db.close()
addStream = AddStream()
app.add_route('/addstream', addStream)        
        