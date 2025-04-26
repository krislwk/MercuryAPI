import falcon
import falcon.asgi
import sqlalchemy
from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.orm import sessionmaker, declarative_base
import base64

#DB Setup
engine = sqlalchemy.create_engine("sqlite:///publicStreams.sqlite")
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class PublicStream(Base):
    __tablename__ = "publicstream"
    streamName = Column(String)
    hostTCP = Column(Integer)
    streamIP = Column(String, primary_key=True)
    thumbnail = Column(LargeBinary, nullable=True)
    
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
            hostTCP = data.get("hostTCP")
            streamIP = data.get("streamIP")
            thumbnail = data.get("thumbnail")
            
            print(streamName)
            print(hostTCP)
            print(streamIP)
            
            if (not streamIP or not streamName or not hostTCP):
                resp.status = falcon.HTTP_400
                resp.media = {"error": "Cannot process request with empty stream ip and/or host tcp."}
                return
            
            alreadyExists = db.query(PublicStream).filter_by(streamIP=streamIP).first()
            if (alreadyExists):
                resp.status = falcon.HTTP_400
                resp.media = {"error": "A stream with this ip already exists."}
                return
            
            thumbnailBase64 = data.get("thumbnail")
            thumbnailBytes = None
            if thumbnail:
                thumbnailBytes = base64.b64decode(thumbnailBase64) #decode from base64

            newStreamItem = PublicStream(streamName = streamName, hostTCP = hostTCP, streamIP = streamIP, thumbnail=thumbnailBytes)
            db.add(newStreamItem)
            db.commit()
            db.refresh(newStreamItem)
            resp.status = falcon.HTTP_200

        finally:
            db.close()
addStream = AddStream()
app.add_route('/addstream', addStream)        


#Endpoint for deleting an existing stream from the public stream database
class DeleteStream:
    async def on_post(self, req, resp):
        db = SessionLocal()
        try:
            data = await req.get_media()
            streamIP = data.get("streamIP")
            
            if (not streamIP):
                resp.status = falcon.HTTP_400
                resp.media = {"error": "Cannot process request with empty stream ip."}
                return
            
            streamToDelete = db.query(PublicStream).filter_by(streamIP=streamIP).first()
            
            if (not streamToDelete):
                resp.status = falcon.HTTP_404
                resp.media = {"error": "No stream found with the given stream ip."}
                return
            
            db.delete(streamToDelete)
            db.commit()
            resp.status =falcon.HTTP_200
            
        finally:
            db.close()
deleteStream = DeleteStream()
app.add_route('/deletestream', deleteStream)

#Endpoint for fetching all existing streams from the public stream database
class FetchStreams:
    async def on_get(self, req, resp):
        db = SessionLocal()
        try:
            streams = db.query(PublicStream).all()
            
            resp.media = [
                {
                    "streamName": item.streamName,
                    "hostTCP": item.hostTCP,
                    "streamIP": item.streamIP,
                    "thumbnail": base64.b64encode(item.thumbnail).decode('utf-8') if item.thumbnail else None
                }
                for item in streams
            ]
            resp.status = falcon.HTTP_200
        finally:
            db.close()
fetchStreams = FetchStreams()
app.add_route('/fetchstreams', fetchStreams)