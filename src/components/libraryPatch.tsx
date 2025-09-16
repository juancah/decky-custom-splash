import {useEffect} from 'react'
import   {useParams,SteamSpinner} from "@decky/ui";
import {
  callable
} from "@decky/api"
const startTimer = callable<[], void>("start_timer");
export default function LibraryPatch({setAppId}) {
    
    const { appid,...rest} = useParams<{ appid: string }>()
  useEffect(() => {
    setAppId(appid)
  }, [appid])
  
  return (
    <>
    <div>LibraryPatch {appid}</div>
    <SteamSpinner/>
    </>
  )
}