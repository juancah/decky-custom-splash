import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  Navigation,
  staticClasses,
  useParams
} from "@decky/ui";
import {
  addEventListener,
  removeEventListener,
  callable,
  definePlugin,
  toaster,
  routerHook
} from "@decky/api"
import logo from '../assets/logo.png'
import { useState } from "react";
import { FaShip } from "react-icons/fa";
import patchLibraryApp from './patchLibraryApp'
// import logo from "../assets/logo.png";

// This function calls the python function "add", which takes in two numbers and returns their sum (as a number)
// Note the type annotations:
//  the first one: [first: number, second: number] is for the arguments
//  the second one: number is for the return value
const add = callable<[first: number, second: number], number>("add");

// This function calls the python function "start_timer", which takes in no arguments and returns nothing.
// It starts a (python) timer which eventually emits the event 'timer_event'
// css: string, appinfo: any
const startTimer = callable<[css: string, appinfo: any], void>("start_timer");

const css = `

`
function Content() {
  const [result, setResult] = useState<number | undefined>();

  const onClick = async () => {
    const result = await add(Math.random(), Math.random());
    setResult(result);
  };

  return (
    <PanelSection title="Panel Section">
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={onClick}
        >
          {result ?? "Add two numbers via Python"}
        </ButtonItem>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem
          layout="below"
        onClick={() => startTimer(css,4278829838)}
        >
          {"Start gyat timer"}
        </ButtonItem>
        <h3>{css}</h3>
      </PanelSectionRow>

      {/* <PanelSectionRow>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <img src={logo} />
        </div>
      </PanelSectionRow> */}

      {/*<PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={() => {
            Navigation.Navigate("/decky-plugin-test");
            Navigation.CloseSideMenus();
          }}
        >
          Router
        </ButtonItem>
      </PanelSectionRow>*/}
    </PanelSection>
  );
};

export default definePlugin(() => {
  console.log("Template plugin initializing, this is called once on frontend startup")

  const libraryPatch = patchLibraryApp()
  // serverApi.routerHook.addRoute("/decky-plugin-test", DeckyPluginRouterTest, {
  //   exact: true,
  // });

  // Add an event listener to the "timer_event" event from the backend
  const listener = addEventListener<[
    test1: string,
    test2: boolean,
    test3: number
  ]>("timer_event", (test1) => {
    console.log("Template got timer_event with:", test1)
    toaster.toast({
      title: "template got timer_event",
      body: `${test1}`
    });
  });

  return {
    // The name shown in various decky menus
    name: "Custom Splash",
    // The element displayed at the top of your plugin's menu
    titleView: <div className={staticClasses.Title}>Custom Splash</div>,
    // The content of your plugin's menu
    content: <Content />,
    // The icon displayed in the plugin list
    icon: <FaShip />,
    // The function triggered when your plugin unloads
    onDismount() {
      console.log("Unloading")
      routerHook.removePatch('/library/app/:appid', libraryPatch)
      removeEventListener("timer_event", listener);
      // serverApi.routerHook.removeRoute("/decky-plugin-test");
    },
  };
});
