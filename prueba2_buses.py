import sqlite3

try:
    cnc = sqlite3.connect("DBBuses.db")
    
    cnc.execute("""Create table if not exists Trabajadores (rut text primary key,
                  nombre text, rol integer, password text)""")#Rol 1 jefe, 2 vendedor, 3 chofer, 4 auxiliar
    
    cnc.execute("""Create table if not exists Rutas (id_ruta integer primary key autoincrement, destino text,
                 tiempo integer, valor integer check (valor > 0), distancia integer check(distancia > 0))""")

    cnc.execute("""Create table if not exists Ventas (id_venta integer primary key autoincrement, rut_trabajador text,
                fecha_venta numeric, hora numeric, total integer, 
                constraint fk_Trabajadores foreign key (rut_trabajador) references Trabajadores(rut))""")

    cnc.execute("""Create table if not exists Buses (patente text primary key, capacidad integer check (capacidad > 0))""")

    cnc.execute("""Create table if not exists Chofer (id_chofer integer primary key autoincrement, rut_chofer text,
                nombre text, minutos_conduccion integer check (minutos_conduccion >= 0), 
                constraint fk_Trabajadores foreign key(rut_chofer) references Trabajadores(rut)) """)
    
    cnc.execute("""Create table if not exists Asistencia(id_asistencia integer primary key autoincrement, id_chofer integer,
                id_viaje integer, asistencia numeric,
                constraint fk_Chofer foreign key(id_chofer) references Chofer(id_chofer),
                constraint fk_Viaje foreign key(id_viaje) references Viajes(id_viaje))""")
    
    cnc.execute("""Create table if not exists Auxiliar (id_auxiliar integer primary key autoincrement, rut_aux text,
                nombre text,
                constraint fk_Trabajadores foreign key(rut_aux) references Trabajadores(rut))""")
    
    cnc.execute("""Create table if not exists Pasajero (rut_pasajero text primary key, nombre text)""")

    cnc.execute("""Create table if not exists Viajes (id_viaje integer primary key autoincrement, patente_bus text,
                id_ruta integer, hora_salida text, fecha text, id_chofer integer, id_auxiliar integer, capacidad integer, 
                constraint fk_bus foreign key(patente_bus) references Buses(patente), 
                constraint fk_ruta foreign key(id_ruta) references Rutas(id_ruta),
                constraint fk_chofer foreign key(id_chofer) references Chofer(id_chofer),
                constraint fk_auxiliar foreign key(id_auxiliar) references Auxiliar(id_auxiliar))""")
    
    cnc.execute("""Create table if not exists Boletos (Folio integer primary key autoincrement, id_venta integer, 
                id_viaje integer, id_pasajero text ,
                constraint fk_venta foreign key(id_venta) references Ventas(id_venta),
                constraint fk_viaje foreign key(id_viaje) references Viajes(id_viaje),
                constraint fk_pasajero foreign key(id_pasajero) references Pasajero(rut_pasajero)) """)

    cnc.commit()
except Exception as a:
    print("ERROR CREANDO TABLAS",a)
finally:
    cnc.close()

class Trabajador:
    def __init__(self, rut:str, nombre:str):
        self.__rut = rut
        self.__nombre = nombre

    @property
    def rut(self):
        return self.__rut
    @property
    def nombre(self):
        return self.__nombre
    
    def lista_pasajeros(self,idviaje):
        try:
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select Boletos.id_pasajero, Pasajero.nombre from Boletos inner join Viajes
                                    on Boletos.id_viaje = Viajes.id_viaje inner join Pasajero 
                                    on Boletos.id_pasajero = Pasajero.rut_pasajero  
                                    where Viajes.id_viaje = ? """, (idviaje),)
            pasajeros = cursor.fetchall()
            if pasajeros:
                return[(pasajero[0], pasajero[1]) for pasajero in pasajeros]
            else:
                return "NO EXISTE LISTADO PARA LA ID SOLICITADA"
        except Exception as a:
            print ("ERROR LISTA PASAJEROS",a)
        finally:
            cnc.close()
    
class Vendedor(Trabajador):
    def __init__(self, rut, nombre):
        super().__init__(rut, nombre)

    def venta(self,nombre,rut,id_viaje):
        from datetime import datetime
        try: 
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select capacidad from Viajes where Viajes.id_viaje = ?""",(id_viaje,))
            capacidad = cursor.fetchone()
            if  capacidad[0] > 0: 
                fecha = datetime.now().strftime("%d/%m/%y")
                hora = datetime.now().strftime("%H:%M:%S")
                cursor = cnc.execute("""Select Rutas.valor from Rutas inner join Viajes
                                    on Rutas.id_ruta = Viajes.id_viaje where id_viaje = ?""", (id_viaje,))
                valor = cursor.fetchone()
                cnc.execute("""Insert into Ventas (rut_trabajador, fecha_venta, hora, total) values (?,?,?,?)""",
                            (self.rut,fecha,hora,valor[0]))
                cnc.execute("""Insert or ignore into Pasajero (rut_pasajero, nombre) values (?,?)""", (rut,nombre)) 
                cursor = cnc.execute("""Select id_venta from Ventas where hora = ?""", (hora,))
                id_venta = cursor.fetchone()
                cnc.execute("""Insert into Boletos (id_venta, id_viaje, id_pasajero) values (?,?,?)""",
                            (id_venta[0],id_viaje,rut))
                cnc.execute("""update Viajes set capacidad = ? where id_viaje = ?""",(capacidad[0]-1,id_viaje,))
                cnc.commit()
                return True
            else:
                print("BUS LLENO")
                return False
        except TypeError:
            print("REVISE LOS DATOS INGRESADOS")        
        except Exception as a:
            print("ERROR VENTA",a)
            return False
        finally:
            cnc.close()
    def boleto(self,rut):#QUE pasa si un mismo rut compora muchos boletos diferentes 
        try:
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select rut_pasajero from Pasajero where rut_pasajero = ?""",(rut,))
            verifica = cursor.fetchone
            if verifica:
                cursor = cnc.execute("""SELECT Boletos.folio, Ventas.fecha_venta, Ventas.hora, Pasajero.nombre AS pasajero_nombre, 
                                    Rutas.destino, Viajes.hora_salida, Viajes.patente_bus, Chofer.nombre, Auxiliar.nombre, 
                                    Ventas.total FROM Boletos INNER JOIN 
                                    Viajes ON Boletos.id_viaje = Viajes.id_viaje
                                INNER JOIN 
                                    Pasajero ON Boletos.id_pasajero = Pasajero.rut_pasajero
                                INNER JOIN 
                                    Rutas ON Viajes.id_ruta = Rutas.id_ruta
                                INNER JOIN 
                                    Ventas ON Boletos.id_venta = Ventas.id_venta
                                INNER JOIN 
                                    Chofer ON Viajes.id_chofer = Chofer.id_chofer
                                INNER JOIN 
                                    Auxiliar ON Viajes.id_auxiliar = Auxiliar.id_auxiliar
                                WHERE 
                                    Pasajero.rut_pasajero = ?""",(rut,))
                resultados = cursor.fetchone()
                if resultados:
                    folio, fecha, hora, pasajero, destino, hora_salida, patente, chofer, auxiliar, total = resultados
                    return(f"""
                        ***********************************************
                        Folio: {folio}                  Fecha: {fecha}
                                                Hora: {hora}


                        Pasajero: {pasajero}
                        Origen: Santiago           Destino: {destino}
                        Hora de salida: {hora_salida}
                        Patente del Bus: {patente}
                        Chofer: {chofer}
                        Auxiliar: {auxiliar}
                        Total pagado: ${total}
                        ***********************************************
                        """)
            else:
                return(f"No se encontraron boletos para el pasajero con RUT {rut}.")

        except Exception as a:
            print("ERROR BOLETOS:", a)
        finally:
            cnc.close()
    
    def anular(self,id_venta):
        try:
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select id_venta from Ventas where id_venta = ?""",(id_venta,))
            datos = cursor.fetchone()
            if datos:
                cursor = cnc.execute("""select Viajes.capacidad, Viajes.id_viaje  from Viajes inner join Boletos
                                     on Viajes.id_viaje = Boletos.id_viaje inner join Ventas
                                     on Boletos.id_venta = Ventas.id_venta
                                    where Ventas.id_venta = ?""",(id_venta,))
                capaci = cursor.fetchone()
                capacidad,id_viaje = capaci
                cnc.execute("""delete from Ventas where id_venta = ?""",(id_venta,))
                cnc.execute("""delete from Boletos where id_venta = ?""",(id_venta,))
                cnc.execute("""update Viajes set capacidad = ? where id_viaje = ?""",(capacidad+1,id_viaje,))
                cnc.commit()
                return True
            else:
                return False
        except Exception as a:
            print("ERROR AL ANULAR",a)
            return False
        finally:
            cnc.close()

    def vista_planificacion(self):
        try:
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select Viajes.patente_bus,Rutas.destino,Viajes.hora_salida,Viajes.fecha,
                                Viajes.capacidad,Chofer.nombre, Auxiliar.nombre from Viajes
                                 inner join
                                 Rutas on Viajes.id_ruta = Rutas.id_ruta
                                 inner join 
                                 Chofer on Viajes.id_chofer = chofer.id_chofer
                                 inner join
                                 Auxiliar on Viajes.id_auxiliar = auxiliar.id_auxiliar""")
            resultador = cursor.fetchall()
            plan = []
            for fila in resultador:
                plan.append(fila)
            return plan
        except Exception as a:
            print("ERROR EN VISUALIZACION PLANES",a)
        finally:
            cnc.close()                    

class Jefe_operaciones(Trabajador):
    def __init__(self, rut, nombre):
        super().__init__(rut, nombre)

    def planificar(self,patente,destino,hora_salida,fecha,id_chofer,id_auxiliar):
        try:
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select minutos_conduccion from Chofer where id_chofer = ?""", (id_chofer,))
            minutos = cursor.fetchone()
            if minutos[0] < 10800:
                cursor = cnc.execute("""select id_ruta from Rutas where destino = ?""", (destino,))
                id_ruta = cursor.fetchone()
                cursor = cnc.execute("""select capacidad from Buses where patente = ?""", (patente,))
                matricula = cursor.fetchone()
                cnc.execute("""insert into Viajes (patente_bus,id_ruta,hora_salida,fecha,id_chofer,id_auxiliar,capacidad)
                            values (?,?,?,?,?,?,?)""", (patente,id_ruta[0],hora_salida,fecha,id_chofer,id_auxiliar,matricula[0]))
                cnc.commit()
                cursor = cnc.execute("""select id_viaje from Viajes order by id_viaje desc limit 1""")
                id_viaje = cursor.fetchone()
                cnc.execute("""insert into Asistencia (id_chofer, id_viaje, asistencia)
                            values (?,?,?)""",(id_chofer,id_viaje[0],0))
                cnc.commit()
                return True
            else:
                print("CHOFER NECESITA DESCANSO")
                return False
        except TypeError:
            return False        
        except Exception as a:
            print("ERROR EN PLANIFICAR",a)
        finally:
            cnc.close()
    
    def horas_conduccion (self,id_chofer):
        try:    
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select minutos_conduccion from Chofer where id_chofer = ?""", (id_chofer,))
            minutos = cursor.fetchone()
            horas = (minutos[0]//60)
            resto = minutos[0]%60
            total = f"Horas: {horas}, Minutos: {resto}"
            return total
        except TypeError as b:
            print ("NO EXISTE EL USUARIO A REVISAR",b)
        except Exception as a:
            print("ERROR EN HORAS CONDUCCION",a)
        finally:
            cnc.close()

    def ver_ventas(self,fecha):
        try:    
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select * from Ventas where fecha_venta = ?""",(fecha,))
            datos = cursor.fetchall()  
            ventas = []  
            if datos:
                for fila in datos:
                    ventas.append(fila)
                return ventas        
            else:
                print("No se encontraron viajes.")
        except Exception as a:
            print ("ERROR VER VENTAS", a)
        finally:
            cnc.close()

class Chofer(Trabajador):
    def __init__(self, rut, nombre):
        super().__init__(rut, nombre)
        self.__rol = "Chofer"
    
    def consulta_ruta(self,id_ruta):
        try:
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select destino,tiempo,distancia from Rutas where id_ruta = ?""",(id_ruta),)
            datos = cursor.fetchone()
            if datos:
                destino,tiempo,distancia = datos
                return f"Destino:{destino} , Distancia: {distancia}, Tiempo estimado: {tiempo}"
            else:
                return "No existe la consulta"
        except Exception as a:
            print("ERROR EN CONSULTA",a)
        finally:
            cnc.close()

    def asistencia(self,id_viaje):
        try:
            cnc = sqlite3.connect("DBBuses.db")
            cursor = cnc.execute("""select id_chofer from Chofer where rut_chofer = ?""",(self.rut,))
            id_chofer = cursor.fetchone()
            cnc.execute("""update Asistencia set asistencia = ? where id_chofer = ? and id_viaje = ?""",
                        (1,id_chofer[0],id_viaje))
            cursor = cnc.execute("""select Rutas.tiempo from Rutas inner join Viajes
                                 on Rutas.id_ruta = Viajes.id_ruta where id_chofer = ?""",(id_chofer[0],))
            minutos = cursor.fetchone()
            cursor = cnc.execute("""select minutos_conduccion from Chofer where id_chofer = ?""",(id_chofer[0],))
            conduccion = cursor.fetchone()
            total = minutos[0] + conduccion [0] 
            cnc.execute("""update Chofer set minutos_conduccion = ? where id_chofer = ?""",(total,id_chofer[0],))
            cnc.commit()
            return True
        except TypeError as b:
            print("NO TE CORRESPONDE ESE VIAJE")
        except Exception as a:
            print("ERROR EN ASISTENCIA",a)
            return False
        finally:
            cnc.close()            

def obtener(rutt):
    try:
        cnc = sqlite3.connect("DBBuses.db")
        cursor = cnc.execute("""select rut, nombre, rol from Trabajadores where rut = ? """, (rutt,))
        datos = cursor.fetchone()
        rut,nombre,rol = datos
        if rol == 1:
            cuenta = Jefe_operaciones(rut,nombre)
        elif rol == 2:
            cuenta = Vendedor(rut,nombre) 
        elif rol == 3:
            cuenta = Chofer(rut,nombre)
        else: 
            cuenta = Trabajador(rut,nombre)
        return cuenta
    except Exception as a:
        print("ERROR EN OBTENER",a)
    finally:
        cnc.close()

import getpass
def menu_principal():
    while True:
        ancho = 90
        print("*" * ancho)
        print("*"+"BIENVENIDO AL SISTEMA".center(88)+"*")
        print("*" * ancho)
        print("1.Ingresar") 
        print("2.Salir")
        print("*" * ancho)
        opcion = input("Seleccione una opción: ")
        if opcion == "1":
            user = input("Rut: ")
            contra = getpass.getpass("Contraseña: ")
            try:
                cnc = sqlite3.connect("DBBuses.db")
                cursor = cnc.execute("""select rut, password, rol from Trabajadores where rut = ? """, (user,))
                verficador = cursor.fetchone()
                if verficador:
                    rut,password,rol = verficador
                    if user == rut and contra == password:
                        print ("Acceso Correcto")
                        cuenta = obtener(rut)
                        if rol == 1:
                            menu_jefe(cuenta)
                        elif rol == 2:
                            menu_vendedor(cuenta)
                        elif rol == 3:
                            menu_chofer(cuenta)
                        else:
                            print("No tiene acceso al sistema")
                    else:
                        print("Error en usuario o contraseña 1")
                else:
                    print("Error en usuario o contraseña 2")
            except Exception as a:
                print("ERROR EN VERIFICACION",a)
            finally:
                cnc.close()
        elif opcion == "2":
            print("Gracias por usar el sistema bancario. ¡Adiós!")
            break
        else:
            print("Opción inválida. Intente nuevamente.")
            input("Presione Enter para continuar...")

def menu_jefe(cuenta):
    while True:
        print("*"*90)
        print("1. Revisar lista de Pasajeros")
        print("2. Planificación de viajes")
        print("3. Revisar horas trabajadas de chofer")
        print("4. Ver Ventas por fecha")
        print("5. Volver al menú principal")
        print("*"*90)
        opcion = input("Seleccione una opción: ")
        if opcion == "1":
            viaje = input("Ingrese el id del viaje a revisar: ")
            print (cuenta.lista_pasajeros(viaje)) 
            input(" ")
        elif opcion == "2":
            patente = input("Ingrese patente: ")
            destino = input("Ingrese destino: ")
            hora_salida = input("Ingresa hora de salida(hh:mm): ")
            fecha = input("Ingresa fecha de viaje(dd/mm/yy): ")
            chofer = (input("Ingresa el id del chofer: "))
            auxiliar = (input("Ingresa id del auxiliar: "))
            if cuenta.planificar(patente,destino,hora_salida,fecha,chofer,auxiliar):
                print ("INGRESO DE VIAJE EXITOSO")
                input("")
            else:
                print ("REVISE LOS DATOS INGRESADOS")
                input("")
        elif opcion == "3":
            chofer = int(input("Ingrese la id del chofer: "))
            print(cuenta.horas_conduccion(chofer))
            input("")
        elif opcion == "4":
            print("DEBE INGRESAR TODO EN VALOR NUMERICO")
            dia = input("Ingrese el dia de busqueda: ")
            if dia.isnumeric():
                mes = input("Ingrese el mes de busqueda: ")
                if mes.isnumeric():
                    año = input("Ingrese el año de busqueda: ")
                    if año.isnumeric():
                        if len(año)>= 2:
                            año = año[-2:]
                            fecha = dia+"/"+mes+"/"+año
                            print(cuenta.ver_ventas(fecha))
                        else:
                            print("Tamaño de año muy corto")    
                    else:
                        print("Formato no aceptado, deben ser números")        
                else:
                    print("Formato no aceptado, deben ser números")            
            else:
                print("Formato no aceptado, deben ser números")                
        elif opcion == "5":
            print("Volviendo al menú principal...")
            break
        else:
            print("Opción inválida. Intente nuevamente.")
            input("Presione Enter para continuar...")

def menu_vendedor(cuenta):
    while True:
        print("*"*90)
        print("1. Revisar lista de Pasajeros")
        print("2. Registrar venta")
        print("3. Ver boleto")
        print("4. Anular Venta")
        print("5. Ver planificaciones")
        print("6. Volver al menú principal")
        print("*"*90)
       
        opcion = input("Seleccione una opción: ")
        if opcion == "1":
            viaje = input("Ingrese el ID del viaje a revisar: ")
            print (cuenta.lista_pasajeros(viaje)) 
            input(" ")
        elif opcion == "2":
            nombre = input("Ingrese nombre pasajero: ")
            rut = input("Ingresa rut pasajero: ")
            id_viaje = (input("Ingresa ID de viaje: "))
            if cuenta.venta(nombre,rut,id_viaje):
                print ("INGRESO DE VENTA EXITOSO")
        elif opcion == "3":
            rut = (input("Ingrese rut pasajero: "))
            print(cuenta.boleto(rut))
            input(" ")
        elif opcion == "4":
            id_venta = input("Ingrese ID VENTA a anular: ")
            if (cuenta.anular(id_venta)):
                print("VENTA ANULADA CON EXITO")
            else:
                print("REVISA LOS DATOS ENTREGADOS")
        elif opcion == "5":
            print(cuenta.vista_planificacion())
        elif opcion == "6":
            print("Volviendo al menú principal...")
            break
        else:
            print("Opción inválida. Intente nuevamente.")
            input("Presione Enter para continuar...")

def menu_chofer(cuenta):
    while True:
        print("*"*90)
        print("1. Revisar lista de Pasajeros")
        print("2. Consultar ruta")
        print("3. Marcar asistencia")
        print("4. Volver al menú principal")
        print("*"*90)
       
        opcion = input("Seleccione una opción: ")
        if opcion == "1":
            viaje = input("Ingrese el id del viaje a revisar: ")
            print (cuenta.lista_pasajeros(viaje)) 
            input(" ")
        elif opcion == "2":
            ruta = input("Ingrese ID ruta: ")
            print(cuenta.consulta_ruta(ruta))
        elif opcion == "3":
            id =(input("Ingrese la ID del viaje: "))
            if cuenta.asistencia(id):
                print("ASISTENCIA INGRESADA CORRECTAMENTE")
        elif opcion == "4":
            print("Volviendo al menú principal...")
            break
        else:
            print("Opción inválida. Intente nuevamente.")
            input("Presione Enter para continuar...")

menu_principal()
            
         