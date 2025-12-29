import os
import subprocess
import glob
import shutil
import traceback
import json
import re
from src.bronco_finder_agent import CorrectorAgent
import src.utils as utils
from datetime import datetime
import pdfplumber

class CorrectionFailed(Exception):
    def __init__(self, student, error_type, message):
        student.error_type = error_type
        student.logs.append(message)
        super().__init__(message)

class CompilationError(CorrectionFailed):
    def __init__(self, student, message):
        super().__init__(student, "ERRO-COMPILACAO", message)

class WrongFilePathError(CorrectionFailed):
    def __init__(self, student, message):
        super().__init__(student, "ARQUIVO-NOME-ERRADO", message)

class OutputFormattingError(CorrectionFailed):
    def __init__(self, student, message):
        super().__init__(student, "FORMATACAO-OUTPUT-ERRADA", message)

class FailedTestcaseError(CorrectionFailed):
    def __init__(self, student, message):
        super().__init__(student, "ERRO-CASOS-TESTE", message)

class Student():
    def __init__(self, student_path):
        self.path = student_path
        self.name = os.path.basename(student_path)
        self.error_type = None
        self.logs = []
        self.num_total_testcases = 0
        self.num_passed_testcases = 0

class LabCorrector():
    def __init__(self, dados_lab):
        self.numero_lab = dados_lab.numero_lab
        self.testcases_path = dados_lab.testcases_path
        self.student_errors_path = dados_lab.student_errors_path
        self.students_path = dados_lab.students_path
        self.error_type_to_correct = dados_lab.error_type_to_correct
        self.do_bronco_detection = dados_lab.do_bronco_detection
        self.student_to_correct = dados_lab.student_to_correct
        self.jump_to_student = dados_lab.jump_to_student 
        self.run_timeout = dados_lab.run_timeout
        self.compile_timeout = dados_lab.compile_timeout
        self.student_folder_files = dados_lab.student_folder_files
        self.array_regexes = dados_lab.array_regexes
        self.correction_function = dados_lab.correction_function
        self.output_types = dados_lab.output_types     
        self.ai_correction_criteria = dados_lab.ai_correction_criteria
        self.ai_correction_introduction_prompt = dados_lab.ai_correction_introduction_prompt
        self.has_report = dados_lab.has_report

        # If only one student, correct using all criteria
        if self.student_to_correct:
            self.error_type_to_correct = 'ALL'

        self.student = None

        self.error_files = [
            "ARQUIVO-NOME-ERRADO.txt",
            "ERRO-COMPILACAO.txt",
            "FORMATACAO-OUTPUT-ERRADA.txt",
            "ERRO-CASOS-TESTE.txt",
            "NO-ERRORS.txt"
        ]

        self.students = self.get_students_list()

        self.remove_error_type_txts()

    def get_students_list(self):
        students = []

        for folder in os.listdir(self.students_path):
            student_path = os.path.join(self.students_path, folder)
            students.append(Student(student_path))

        for file in self.error_files:
            error_file_path = os.path.join(self.student_errors_path, file)
            os.makedirs(self.student_errors_path, exist_ok=True)
            if not os.path.isfile(error_file_path):
                continue
            with open(error_file_path, "r") as f:
                for line in f:
                    student_name = line.strip()
                    if student_name:
                        for student in students:
                            if student.name == student_name:
                                student.error_type = file[:-4]
        return sorted(students, key=lambda x: x.name)                          
            
    def clear_logs_file(self):
        logs_correcao_path = self.student.path + "/logs_correcao_auto.txt"
        try:
            open(logs_correcao_path, "w").close()
        except:
            pass

    def log_errors(self, encoding):
        logs_correcao_path = self.student.path + "/logs_correcao_auto.txt"
        with open(logs_correcao_path, "a", encoding=encoding) as logs:
            print(f"{self.student.error_type}\n", file=logs)                
            for error_log in self.student.logs:
                print(error_log, file=logs)

    def add_log(self, message, encoding):
        logs_correcao_path = self.student.path + "/logs_correcao_auto.txt"
        with open(logs_correcao_path, "a", encoding=encoding) as logs:
            print(message, file=logs)                

    def remove_outputs_folder(self):
        outputs_path = os.path.join(self.student.path, "outputs")
        if os.path.exists(outputs_path) and os.path.isdir(outputs_path):
            shutil.rmtree(outputs_path)

    def remove_unwanted_files(self):
        for f in os.listdir(self.student.path):
            full_path = os.path.join(self.student.path, f)
            _, extension = os.path.splitext(f)            
            if f not in self.student_folder_files and extension not in self.student_folder_files:
                if os.path.isfile(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)

    def remove_error_type_txts(self):
        for file in self.error_files:
            error_file_path = os.path.join(self.student_errors_path, file)
            if os.path.isfile(error_file_path):
                os.remove(error_file_path)

    def create_error_type_txts(self):
        for student in self.students:
            error_file = f"{student.error_type}.txt"
            error_file_path = os.path.join(self.student_errors_path, error_file)
            with open(error_file_path, "a") as file:
                file.write(student.name + "\n")

    def get_and_process_outputs(self, testcase):
        output_paths = glob.glob(f'{self.student.path}/Lab*.txt')
        output_folder = os.path.join(self.student.path, 'outputs')
        final_output_path = os.path.join(output_folder, f"{testcase}.txt")     
        os.makedirs(output_folder, exist_ok=True)
        outputs = {}
        for output_path in output_paths:
            current_final_output_path = final_output_path
            filename = os.path.basename(output_path)
            output_type = None
            for _type in self.output_types:
                if _type.lower() in filename.lower():
                    output_type = _type
                    inner_output_folder = os.path.join(output_folder, _type)
                    os.makedirs(inner_output_folder, exist_ok=True)
                    current_final_output_path = os.path.join(inner_output_folder, f"{testcase}.txt")
                    break

            if not self.output_types or output_type:
                shutil.copy(output_path, current_final_output_path)

            os.remove(output_path)

            # Append to student output the answer to the testcase
            with open(current_final_output_path, "a") as f:
                answers_path = os.path.join(self.testcases_path, testcase, f'saida{self.numero_lab}.json')
                with open(answers_path, "r", encoding="utf-8") as answers_file:
                    answers = json.load(answers_file)
                    f.write("\n\nGABARITO:\n")
                    f.write(json.dumps(answers.get("order", []), ensure_ascii=False, indent=2) + "\n")
                       
            if self.output_types and not output_type:
                continue

            lines = utils.read_file_lines(current_final_output_path)

            if not self.output_types:
                outputs["default"] = lines
                continue

            outputs[output_type] = lines
        
        if not self.output_types:
            if "default" not in outputs:
                raise FailedTestcaseError(
                self.student,
                f"Nao criou o arquivo de saida\n"
            )

        missing_types = []
        for _type in self.output_types:
            if _type not in outputs:
                missing_types.append(_type)
        if missing_types:
            missing_str = ", ".join(f"{t}.txt" for t in missing_types)
            raise FailedTestcaseError(
                self.student,
                f"Nao criou os arquivos de saida: {missing_str}\n"
            )
            
        return outputs
    
    def get_report(self):
        report_path = glob.glob(f'{self.student.path}/Lab*.pdf')[0]
        text = ''
        with pdfplumber.open(report_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    lines = [line for line in txt.split('\n') if not line.strip().isdigit()]
                    text += '\n'.join(lines) + '\n'
        return text.strip()

        
    def get_student_code(self):
        cpp_path = glob.glob(f'{self.student.path}/Lab*.cpp')
        if not cpp_path:
            raise WrongFilePathError(self.student, "Nao enviou o arquivo .cpp\n")
        return ''.join(utils.read_file_lines(cpp_path[0]))

    def compile_student_code(self):
        compiler = r"C:\msys64\mingw64\bin\g++.exe"  # Caminho do g++ no MSYS2

        if os.path.isdir(self.student.path):
            cpp_path = os.path.join(self.student.path, "Lab*.cpp")

            try:
                result = subprocess.run(
                    f'"{compiler}" {cpp_path} -o "{self.student.path}/a.exe"',
                    shell=True,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=self.compile_timeout
                )

                # Printar warnings nos logs
                if result.returncode == 0 and result.stderr:
                    self.add_log(
                        f"WARNINGS NA COMPILACAO:\n{result.stderr.decode('utf-8', errors='replace')}",
                        encoding="utf-8"
                    )

            except subprocess.CalledProcessError as e:
                raise CompilationError(
                    self.student,
                    f"Código de saida: {e.returncode}\nTRACEBACK:\n{e.stderr.decode('utf-8', errors='replace')}"
                )

            except subprocess.TimeoutExpired:
                raise CompilationError(self.student, "Tempo limite de compilacao excedido.")

            except Exception as e:
                raise CompilationError(self.student, f"Ocorreu um erro inesperado na compilacao: {e}")


    def run_student_code(self, testcase):
        testcase_path = os.path.join(self.testcases_path, testcase)
        input_file = os.path.join(testcase_path, f"entrada{self.numero_lab}.txt")
        shutil.copy(input_file, self.student.path)
        input_file = os.path.join(testcase_path, f"Entrada{self.numero_lab}.txt")
        shutil.copy(input_file, self.student.path)

        try:
            subprocess.run(
                './a.out', 
                cwd=self.student.path, 
                shell=True, 
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.run_timeout
            )
        except subprocess.CalledProcessError as e:
            raise FailedTestcaseError(self.student, f"Erro na execucao do caso teste {testcase}.\nCodigo de saida: {e.returncode}\n")
        except subprocess.TimeoutExpired:
            raise FailedTestcaseError(self.student, f"Tempo limite de execucao do caso teste {testcase} excedido")
        except Exception as e:
            raise FailedTestcaseError(self.student, f"Ocorreu um erro inesperado na execucao do caso teste {testcase}: {e}\n")

    def check_fopen_path(self, student_code):
        pattern_entrada = rf'"([^"]*entrada{self.numero_lab}[^"]*)"'
        nome_entrada_correto = re.search(pattern_entrada, student_code, flags=re.IGNORECASE) is not None
        if not nome_entrada_correto:
            raise WrongFilePathError(self.student, "Erro no nome do arquivo de entrada\n")

        if not self.output_types:
            pattern_saida = rf'"Lab{self.numero_lab}_[A-Za-z0-9_]+\.txt"'
            nome_saida_correto = re.search(pattern_saida, student_code, flags=re.IGNORECASE) is not None
            if not nome_saida_correto:
                raise WrongFilePathError(self.student, "Erro no nome do arquivo de saída\n")

        else:
            erros = []
            for output_type in self.output_types:
                pattern_saida_tipo = (
                    rf'"Lab{self.numero_lab}_[A-Za-z0-9_]+_{re.escape(output_type)}\.txt"'
                )

                if re.search(pattern_saida_tipo, student_code, flags=re.IGNORECASE) is None:
                    erros.append(f"Arquivo de saída para tipo '{output_type}' não encontrado")

            if erros:
                raise WrongFilePathError(self.student, "\n".join(erros))

    def correct_code(self):
        code = self.get_student_code()
        if self.do_bronco_detection:
            if self.has_report:
                report_text = self.get_report()
                self.detect_bronco({
                    "Código": code,
                    "Texto Relatório": report_text
                })
            else:
                self.detect_bronco(({
                    "Código": code,
                }))
        self.check_fopen_path(code)
    
    def correct_output(self, testcase):
        self.run_student_code(testcase)
        outputs = self.get_and_process_outputs(testcase)
        self.apply_output_correction_criteria(testcase, outputs)

    def apply_output_correction_criteria(self, testcase, outputs):  
        failed_testcase_errors = ""
        output_formatting_errors = ""

        for output in outputs:  
            lines = outputs[output]
            
            # Get the correct answers and line matching patterns
            answers_path = os.path.join(self.testcases_path, testcase, f'saida{self.numero_lab}.json')
            with open(answers_path, "r", encoding="utf-8") as answers_file:
                answers = json.load(answers_file)
            
            # Correct list of values the student printed on output
            student_values = utils.get_first_matches_in_many_matching_lines(lines, self.array_regexes["lines"], self.array_regexes["values"])

            # If student list is not right, raise error
            success, comment = self.correction_function(student_values, answers)
            if not success:
                failed_testcase_errors += f"Caso teste: {testcase}: {output}: {comment}\n"

        if output_formatting_errors:
            output_formatting_errors += "\n"
            raise OutputFormattingError(self.student, output_formatting_errors)

        if failed_testcase_errors:
            failed_testcase_errors += "\n"
            raise FailedTestcaseError(self.student, failed_testcase_errors)

    def detect_bronco(self, info_dict):
        corrector_agent = CorrectorAgent(self.ai_correction_criteria)
        
        prompt = (
            self.ai_correction_introduction_prompt
            + "\n\nCritérios de correção:\n\n"
            + "\n\n".join(self.ai_correction_criteria)
            + "\n\nInformações do aluno:\n\n"
            + "\n\n".join(f"{key}:\n{value}" for key, value in info_dict.items())
        )


        response = corrector_agent.respond(prompt)
        
        logs_bronco_path = self.student.path + "/logs_correcao_bronco.txt"
        with open(logs_bronco_path, "w") as logs:
            for line in response:
                print(line, file=logs)                

    def make_student_correction(self):
        try:
            self.correct_code()
            self.compile_student_code()
        except (CompilationError, WrongFilePathError):
            return
        for testcase in os.listdir(self.testcases_path):
            try:
                self.correct_output(testcase)
                self.student.num_passed_testcases += 1
            except (FailedTestcaseError, FailedTestcaseError, OutputFormattingError):
                continue
        if not self.student.logs:
            self.student.error_type = "NO-ERRORS"

    def make_correction(self):
        try:
            correct_all_students = (self.student_to_correct is None)
            # If any student error is missing, correct all
            for student in self.students:
                if student.error_type is None:
                    self.error_type_to_correct = 'ALL'
                    correct_all_students = True
                    break
            students_to_correct = [student for student in self.students if (self.error_type_to_correct == 'ALL' or student.error_type == self.error_type_to_correct)]
            if not correct_all_students:
                students_to_correct = [student for student in students_to_correct if student.name.startswith(self.student_to_correct)]
            progress = 1
            start = datetime.now()
            for student in students_to_correct:
                if self.jump_to_student and student.name != self.jump_to_student:
                    progress += 1
                    continue
                if student.name == self.jump_to_student:
                    self.jump_to_student = None
                self.student = student
                start_student = datetime.now()
                print(f"Correcting... ({progress}/{len(students_to_correct)}). Current student: {student.name}")
                progress += 1
                self.clear_logs_file()
                self.remove_outputs_folder()
                self.make_student_correction()
                self.remove_unwanted_files()
                self.add_log(f"{"-"*25}\nLOGS ERROS:\n{"-"*25}\n", encoding="utf-8")
                self.log_errors(encoding="utf-8")
                self.remove_unwanted_files()
                end_student = datetime.now()
                total_seconds = (end_student - start_student).total_seconds()
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                print(f"Time spent: {minutes} min {seconds:.3f} s")
            self.create_error_type_txts()
            end = datetime.now()
            total_seconds = (end - start).total_seconds()
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            print(f"Correction ended successfully.\nTotal time spent: {minutes} min {seconds:.3f} s\n")
        except Exception as e:
            print(f"Correction failed due to error: {e}")
            traceback.print_exc()



