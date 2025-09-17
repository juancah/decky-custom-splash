import { useEffect } from 'react'
import { useParams, SteamSpinner } from "@decky/ui";
import {
  callable
} from "@decky/api"
// css: string, appinfo: any
const startTimer = callable<[css: string, appinfo: any], void>("start_timer");

const css = `
.loadingthrobber_Container_3sa1N.loadingthrobber_PreloadThrobber_1-epa,
.loadingthrobber_Container_3sa1N.loadingthrobber_ContainerBackground_2ngG3 {
    
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
.truck  { animation: truck 4s   0.080s ease infinite; }
.wheels  { animation: truck 4s   0.001s ease infinite; }
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
  0%   { }
  6%   { transform: translateY(0px); }
  7%   { transform: translateY(-6px); }
  9%   { transform: translateY(0px); }
  10%   { transform: translateY(-1px); }
  11%   { transform: translateY(0px); }
  100%   { }
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
        transform: scale(1);
    }
    100% {
        transform: scale(1.15); /* subtle zoom in */
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

  const handleSteamAppStateChange = async (update) => {
    const gameData = appStore.GetAppOverviewByAppID(Number(appid));
    const payload = {
      display_name: gameData?.display_name ?? gameData?.name ?? "Unknown",
      appid: Number(appid)
    };
    // await so you can catch errors
    await startTimer(css, payload);

  }
  useEffect(() => {
    const reg = SteamClient.GameSessions.RegisterForAppLifetimeNotifications(
      handleSteamAppStateChange
    );

    return () => {
      try { reg.unregister(); } catch (e) { /* ignore */ }
    };
  }, [appid]); // re-register if appid changes

  return (
    <>
      <div style={{ height: '100vh' }}>
        <SteamSpinner />
      </div>
      <div>LibraryPatch {appid}</div>
    </>
  )
}