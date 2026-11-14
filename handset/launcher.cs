using System;
using System.Diagnostics;
using System.IO;

namespace IpPlus
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                Environment.CurrentDirectory = baseDir;

                Environment.SetEnvironmentVariable("COMPlus_LoadFromRemoteSources", "1");
                Environment.SetEnvironmentVariable("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "--enable-features=PlatformHEVCDecoderSupport");
                Environment.SetEnvironmentVariable("WEBVIEW2_DEFAULT_BACKGROUND_COLOR", "0");

                string venvPythonW = Path.Combine(baseDir, "venv", "Scripts", "pythonw.exe");
                string venvPython = Path.Combine(baseDir, "venv", "Scripts", "python.exe");
                string guiScript = Path.Combine(baseDir, "handset", "gui.py");

                // Priority 1: Completely silent GUI execution via pythonw.exe (No console window)
                if (File.Exists(venvPythonW) && File.Exists(guiScript))
                {
                    ProcessStartInfo psi = new ProcessStartInfo();
                    psi.FileName = venvPythonW;
                    psi.Arguments = "\"" + guiScript + "\"";
                    psi.WorkingDirectory = baseDir;
                    psi.UseShellExecute = false;
                    psi.CreateNoWindow = true;
                    psi.WindowStyle = ProcessWindowStyle.Hidden;
                    Process.Start(psi);
                    return;
                }

                // Priority 2: Standard venv python if pythonw is missing
                if (File.Exists(venvPython) && File.Exists(guiScript))
                {
                    ProcessStartInfo psi = new ProcessStartInfo();
                    psi.FileName = venvPython;
                    psi.Arguments = "\"" + guiScript + "\"";
                    psi.WorkingDirectory = baseDir;
                    psi.UseShellExecute = false;
                    psi.CreateNoWindow = true;
                    psi.WindowStyle = ProcessWindowStyle.Hidden;
                    Process.Start(psi);
                    return;
                }

                // Priority 3: Fallback to ip+.bat if dependencies are not yet installed
                string batPath = Path.Combine(baseDir, "ip+.bat");
                if (File.Exists(batPath))
                {
                    ProcessStartInfo psi = new ProcessStartInfo();
                    psi.FileName = "cmd.exe";
                    psi.Arguments = "/c \"" + batPath + "\"";
                    psi.WorkingDirectory = baseDir;
                    psi.UseShellExecute = true;
                    Process.Start(psi);
                }
            }
            catch
            {
                // Silent fail-safe
            }
        }
    }
}
