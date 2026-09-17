import Link from "next/link";

import type { EmployeeListItem } from "@/lib/api";


export function EmployeeTable({ employees }: { employees: EmployeeListItem[] }) {
  return (
    <div className="table-frame">
      <table aria-label="Colaboradores" className="data-table">
        <thead>
          <tr>
            <th scope="col">Colaborador</th>
            <th scope="col">Cargo canônico</th>
            <th scope="col">Base</th>
            <th scope="col">Senioridade</th>
            <th scope="col">Status</th>
            <th scope="col" className="action-column">
              Ação
            </th>
          </tr>
        </thead>
        <tbody>
          {employees.map((employee) => (
            <tr key={employee.id}>
              <td>
                <strong>{employee.name}</strong>
                <span className="cell-detail">{employee.employee_number}</span>
              </td>
              <td>{employee.role_name}</td>
              <td>{employee.base_location}</td>
              <td>{employee.seniority_level}</td>
              <td>
                <span className={`status ${employee.active ? "status-active" : "status-inactive"}`}>
                  {employee.active ? "Ativo" : "Inativo"}
                </span>
              </td>
              <td className="action-column">
                <Link
                  aria-label={`Abrir perfil de ${employee.name}`}
                  className="text-link"
                  href={`/colaboradores/${employee.id}`}
                >
                  Ver perfil
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
