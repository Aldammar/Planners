import csv
import signal
import subprocess
import time
import psutil
import pyRAPL
import os
import argparse
import glob

class PandaPIEnergyMeasurement:
    def __init__(self, input_directory):
        self.input_directory = input_directory
        self.domain_file = os.path.join('../../', input_directory, 'domain.hddl')
        self.problem_files = [file for file in glob.glob(os.path.join(input_directory, '*.hddl')) if 'domain.hddl' not in file]
        self.current_directory = os.path.dirname(os.path.abspath(__file__))
        self.domain_directory = os.path.basename(os.path.dirname(self.domain_file))
        self.pandaPIparser = os.path.join(self.current_directory, 'pandaPIparser')
        self.pandaPIgrounder = os.path.join(self.current_directory, 'pandaPIgrounder')
        self.pandaPIengine = os.path.join(self.current_directory, 'pandaPIengine')
        self.timeout_occurred = False
        pyRAPL.setup()

    def run_command(self, command, timeout=1800):
        if not self.timeout_occurred:
            try:
                process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
                process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                print(f"Command '{command}' timed out after {timeout} seconds and was killed")
                self.timeout_occurred = True
            except subprocess.CalledProcessError as e:
                print(f"Command '{command}' failed with return code {e.returncode}")

    def clean_system_and_wait(self):
        while not self.is_system_idle():
            print("Waiting for system to become idle...")
            time.sleep(5)
        print("System is idle. Ready to start measurement.")

    def is_system_idle(self, cpu_threshold=5.0, memory_threshold=20.0):
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        print(f"CPU Usage: {cpu_usage}%")
        print(f"Memory Usage: {memory_usage}%")
        
        return cpu_usage < cpu_threshold and memory_usage < memory_threshold

    def write_timeout_csv(self, filename, functions):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['label', 'timestamp', 'duration', 'pkg', 'dram', 'socket'])
            for func in functions:
                writer.writerow([func.__name__, 0, 0, 0, 0, 0])

    def measure_energy(self):
        
        # Create the directory and change to it
        if not os.path.exists(self.domain_directory):
            os.makedirs(self.domain_directory)
        os.chdir(self.domain_directory)

        for problem_file in self.problem_files:
            self.timeout_occurred = False
            problem_file_name = os.path.splitext(os.path.basename(problem_file))[0]
            parsed_file = 'temp.parsed'
            psas_file = f"{os.path.splitext(os.path.basename(self.domain_file))[0]}-{problem_file_name}.psas"
            log_file = 'panda.log'
            plan_file = 'plan_file'

            if not os.path.exists(problem_file_name):
                os.makedirs(problem_file_name)
            os.chdir(problem_file_name)

            csv_filename = f"{problem_file_name}.csv"
            csv_output = pyRAPL.outputs.CSVOutput(csv_filename, append=False)

            print(f'Solving problem instance: {problem_file_name}')

            @pyRAPL.measureit(number=30, output=csv_output)
            def Parsing():
                print(f"\033[91m{'run_pandaPIparser'}\033[0m")
                command = f"{self.pandaPIparser} {self.domain_file} {'../../' + problem_file} {parsed_file}"
                return self.run_command(command)

            @pyRAPL.measureit(number=30, output=csv_output)
            def run_pandaPIgrounder():
                print(f"\033[91m{'run_pandaPIgrounder'}\033[0m")
                command = f"{self.pandaPIgrounder} -q -i {parsed_file} {psas_file}"
                return self.run_command(command)

            @pyRAPL.measureit(number=30, output=csv_output)
            def run_pandaPIengine():
                print(f"\033[91m{'run_pandaPIengine'}\033[0m")
                command = f'{self.pandaPIengine} -g none --heuristic="rc2(add)" {psas_file} >> {log_file}'
                return self.run_command(command)

            @pyRAPL.measureit(number=30, output=csv_output)
            def run_pandaPIparser_convert():
                command = f"{self.pandaPIparser} -c {log_file} {plan_file}"
                return self.run_command(command)

            command_functions = [
                run_pandaPIparser,
                run_pandaPIgrounder,
                run_pandaPIengine,
                run_pandaPIparser_convert
            ]

            self.clean_system_and_wait()
            for command_function in command_functions:
                if self.timeout_occurred:
                    break
                command_function()
                self.clean_system_and_wait()

            if self.timeout_occurred:
                self.write_timeout_csv(csv_filename, command_functions)
            else:
                csv_output.save()
            os.chdir('../')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run PandaPI commands and measure energy consumption.')
    parser.add_argument('input_directory', type=str, help='Path to the directory containing domain and problem files')
    args = parser.parse_args()

    panda_pi_energy = PandaPIEnergyMeasurement(args.input_directory)
    panda_pi_energy.measure_energy()
