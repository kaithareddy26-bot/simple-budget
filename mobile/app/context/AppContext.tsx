import React from "react";
const AppContext = React.createContext({
  jwt: "" as string,
  setJwt: (jwt: string) => {},
});
export default AppContext;
