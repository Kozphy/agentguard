import { app, BrowserWindow } from "electron";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { AgentRegistry } from "./agents/registry.js";
import { GitService } from "./git/service.js";
import { registerIpcHandlers } from "./ipc/register.js";
import { ElectronDirectoryPicker, WorkspaceService } from "./workspace/service.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function createServices() {
  const git = new GitService();
  const workspace = new WorkspaceService(git, new ElectronDirectoryPicker());
  const agents = new AgentRegistry();
  return { git, workspace, agents };
}

function createWindow(): BrowserWindow {
  const win = new BrowserWindow({
    width: 1100,
    height: 760,
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    title: "AgentGuard Workbench",
  });

  const devServerUrl = process.env.VITE_DEV_SERVER_URL;
  if (devServerUrl) {
    void win.loadURL(devServerUrl);
  } else {
    void win.loadFile(path.join(__dirname, "../renderer/index.html"));
  }

  return win;
}

app.whenReady().then(() => {
  const services = createServices();
  registerIpcHandlers(services);
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
