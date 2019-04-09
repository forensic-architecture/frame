1. Install
```
    pip3 install git+https://github.com/scztt/frame
```
2. Create a settings.yaml file containing:
```
    events:
        test_video:                                         # unique event name
            name: Test Video                                # descriptive name    
            type: PlayVideo                                 # Must be PlayVIdeo
            schedule: every().day.at("12:02:55")            # schedule string follows syntax of https://github.com/dbader/schedule                            
            # schedule: every(3).minutes
            url: file:///Users/fsc/Desktop/video.mp4       
            # url: http://artificia.org/jsjsjs.mp4          # remote urls should work also, but untested
```
3. Run
```
    frame ~/Desktop/settings.yaml
```
