# Frame
Automate video schedules with YAML.

## Run from command line 
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
## Develop
1. Clone
```
    git clone https://github.com/scztt/frame
```
2. Create development environment through [pipenv](https://github.com/pypa/pipenv)
```
    cd frame
    pipenv shell
```
3. Run in dev
```
    python frame/frame.py frame/default.yaml
```

## Production 
Frame is designed for automating schedules in exhibition or exhibition-like
contexts. You can package a particular config as a standalone Mac application,
so that running the schedule in an exhibition context is as easy as
double-clicking the icon on a dedicated Mac Mini, or equivalent. 

When Frame is packaged, installation becomes as simple as sending a folder with
the videos that your config plays (ensuring that they are at the same absolute
paths as specified in the config you use to package Frame), and the Mac app
file.

### Packaging Mac app
Create a file at frame/default.yaml. Frame will default to using this config if
no settings.yaml is explicitly provided as an argument.

Once this is created, inside the `pipenv shell` from the setup in the Develop
section above
```
    pip install py2app
    python application/mac/setup.py py2app
```

The packaged application should now be in `application/Mac/dist/frame.app`.

### Using a dedicated Mac
If you are using a dedicated Mac for the exhibition, follow these steps to
ensure that Frame plays your video smoothly.

#### Turning the computer on and off at night.
* System Preferences -> Energy Saver -> Schedule..
* Set to ‘Start up or wake’ at some time each day
* Set to ‘Shut down’ at some time each day.

#### Automatic Login
* System Preferences -> Users & Groups -> Login Options
* From the 'Automatic Login' dropdown, select the user.

Note that you will not be able to configure automatic login for a User if
FileVault or some other encryption at rest is used on the computer.

#### Startup Items
Add the Frame app as a Login Item for the user with automatic login. 
* Systems Preferences -> Users & Groups -> ‘+’, and add ‘Frame’. Make sure that you have no other startup items to ensure that the video plays. 

