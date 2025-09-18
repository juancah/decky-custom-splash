import { useEffect, useState, useRef } from 'react'
import { useParams, SteamSpinner } from "@decky/ui";
import {
  callable
} from "@decky/api"
// css: string, appinfo: any
const startTimer = callable<[css: string, appinfo: any], void>("start_timer");
const stopTimer = callable<[css: string, appinfo: any], void>("stop_timer");

const css = `
.loadingthrobber_Container_3sa1N.loadingthrobber_PreloadThrobber_1-epa,
.loadingthrobber_Container_3sa1N.loadingthrobber_ContainerBackground_2ngG3 {
    
}
.loadingthrobber_ContainerBackground{
z-index:100;
}
.loadingthrobber_Container_3sa1N{
  position: relative;
}
#decky_inject_h1{
    margin: 6px 0px 0px;
    font-size: 35px;
    text-align: center;
    color: rgb(255, 255, 255);
    text-shadow: rgba(0, 0, 0, 0.7) 0px 1px 2px;
}
.loadingthrobber_SpinnerLoaderContainer_3CN5D{
   width: 100%;
   height:100%;
   justify-content: center;
   z-index:10;
   position: relative;

}
.loop-wrapper {
    margin: 0 auto;
    position: relative;
    display: block;
    width: 100%;
    height: 113px;
    overflow: hidden;
    border-bottom: 3px solid #fff;
    color: #fff;
    display: flex;
    align-items: end;
}
.mountain {
  position: absolute;
  right: -900px;
  bottom: -20px;
  width: 2px;
  height: 2px;
  box-shadow: 
    0 0 0 50px #4DB6AC,
    60px 50px 0 70px #4DB6AC,
    90px 90px 0 50px #4DB6AC,
    250px 250px 0 50px #4DB6AC,
    290px 320px 0 50px #4DB6AC,
    320px 400px 0 50px #4DB6AC
    ;
  transform: rotate(130deg);
  animation: mtn 20s linear infinite;
}
.hill {
  position: absolute;
  right: -900px;
  bottom: -50px;
  width: 400px;
  border-radius: 50%;
  height: 20px;
  box-shadow: 
    0 0 0 50px #4DB6AC,
    -20px 0 0 20px #4DB6AC,
    -90px 0 0 50px #4DB6AC,
    250px 0 0 50px #4DB6AC,
    290px 0 0 50px #4DB6AC,
    620px 0 0 50px #4DB6AC;
  animation: hill 4s 2s linear infinite;
}
.tree, .tree:nth-child(2), .tree:nth-child(3) {
  position: absolute;
  height: 100px; 
  width: 35px;
  bottom: 0;
  background: url(https://s3-us-west-2.amazonaws.com/s.cdpn.io/130015/tree.svg) no-repeat;
}
.rock {
  margin-top: -17%;
  height: 2%; 
  width: 2%;
  bottom: -2px;
  border-radius: 20px;
  position: absolute;
  background: #ddd;
}
.truck, .wheels {
  transition: all ease;
  width: 85px;
  margin-right: -60px;
  bottom: 0px;
  right: 50%;
  position: absolute;
  background: #eee;
}
.truck {
  background: url(https://s3-us-west-2.amazonaws.com/s.cdpn.io/130015/truck.svg) no-repeat;
  background-size: contain;
  height: 60px;
  position:relative;
  left:0;
}
.truck:before {
  content: " ";
  position: absolute;
  width: 25px;
  box-shadow:
    -30px 28px 0 1.5px #fff,
     -35px 18px 0 1.5px #fff;
}
.wheels {
  background: url(https://s3-us-west-2.amazonaws.com/s.cdpn.io/130015/wheels.svg) no-repeat;
  height: 15px;
  margin-bottom: 0;
}

.tree  { animation: tree 3s 0.000s linear infinite; }
.tree:nth-child(2)  { animation: tree2 2s 0.150s linear infinite; }
.tree:nth-child(3)  { animation: tree3 8s 0.050s linear infinite; }
.rock  { animation: rock 4s   -0.530s linear infinite; }
.truck {
  animation: truck 4s linear infinite;
}

.wheels {
  animation: truck 4s linear infinite;
}

.truck:before { animation: wind 1.5s   0.000s ease infinite; }


@keyframes tree {
  0%   { transform: translate(1350px); }
  50% {}
  100% { transform: translate(-50px); }
}
@keyframes tree2 {
  0%   { transform: translate(650px); }
  50% {}
  100% { transform: translate(-50px); }
}
@keyframes tree3 {
  0%   { transform: translate(2750px); }
  50% {}
  100% { transform: translate(-50px); }
}

@keyframes rock {
  0%   { right: -200px; }
  100% { right: 2000px; }
}
@keyframes truck {
  0%   { transform: translateX(-10vw) translateY(0); }
  7%   { transform: translateX(0vw) translateY(-6px); }   /* bounce entering */
  9%   { transform: translateX(2vw) translateY(0); }
  10%  { transform: translateX(3vw) translateY(-1px); }
  11%  { transform: translateX(4vw) translateY(0); }
  50%  { transform: translateX(50vw) translateY(0); }     /* middle */
  93%  { transform: translateX(93vw) translateY(0); }     /* edge still visible */
  100% { transform: translateX(110vw) translateY(0); }    /* fully off right */
}


@keyframes wind {
  0%   {  }
  50%   { transform: translateY(3px) }
  100%   { }
}
@keyframes mtn {
  100% {
    transform: translateX(-2000px) rotate(130deg);
  }
}
@keyframes hill {
  100% {
    transform: translateX(-2000px);
  }
}
@keyframes ps5-zoom {
    0% {
        transform: scale(1) translate(0%, 0%);
    }
    25% {
        transform: scale(1.05) translate(-2%, -1%);
    }
    50% {
        transform: scale(1.1) translate(-4%, -2%);
    }
    75% {
        transform: scale(1.08) translate(-3%, -1%);
    }
    100% {
        transform: scale(1.12) translate(-5%, -3%);
    }
}
/* Top cinematic bar */
.cinema-bar-top,
.cinema-bar-bottom {
    position: absolute;
    left: 0;
    width: 100%;
    height: 12vh; /* 20% of viewport height */
    background-color: rgb(9 9 9 / 28%);
    z-index: 999; /* above hero image */
    opacity: 0;
    animation: fade-in-bars 5s forwards; /* slowly appear over 5s */
}

/* Position top/bottom */
.cinema-bar-top { top: 0; }
.cinema-bar-bottom { bottom: 0; }

/* Fade-in animation */
@keyframes fade-in-bars {
    0% { opacity: 0; }
    100% { opacity: 1; }
}
}

`

/* .loadingthrobber_Container_3sa1N img {
  opacity:1;
  height: 200px;
  width: 250px;
} */
export default function LibraryPatch() {

  const { appid, ...rest } = useParams<{ appid: string }>()
  const [gameRunning, setGameRunning] = useState(false)
  const gameRunningRef = useRef(gameRunning);
  const prevGameRunningRef = useRef<boolean>(false);
  useEffect(() => {
    gameRunningRef.current = gameRunning;
  }, [gameRunning]);

  const handleSteamAppStateChange = (update: AppState) => {
    const currentAppIdNum = appid ? Number(appid) : null
    if (currentAppIdNum === null) return
    if (update.unAppID !== currentAppIdNum) return // ignore other apps

    // update refs/state
    setGameRunning(update.bRunning)
    prevGameRunningRef.current = update.bRunning
  }



  useEffect(() => {
    const triggerEvent = async () => {
      console.log('EVENT TRIGGERED FOR ', appid)
      const gameData = appStore.GetAppOverviewByAppID(Number(appid));
      const payload = {
        display_name: gameData?.display_name ?? gameData?.name ?? "Unknown",
        appid: Number(appid)
      };
      // await so you can catch errors
      await startTimer(css, payload);
    }
    triggerEvent()


  }, []); // re-register if appid changes
  useEffect(() => {

    console.log('Library patch mounted', appid)
    return () => {
      console.log("STOP timer called!1")
      if (gameRunningRef.current) {
        setTimeout(() => {
          stopTimer();
        }, 4000);
      } else {
        stopTimer()
      }
    };
  }, [])



  useEffect(() => {
    const reg = SteamClient.GameSessions.RegisterForAppLifetimeNotifications(
      handleSteamAppStateChange
    );
    return () => {
      try {
        reg.unregister();

      } catch (e) { /* ignore */ }
    };
  });
  return (
    <>
      <div style={{ height: '100vh' }}>
        <SteamSpinner />
      </div>
    </>
  )
}