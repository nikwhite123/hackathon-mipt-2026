import { Result, Button } from "antd"
import { Link } from "react-router-dom"

export default function NotFoundPage() {
  return (
    <Result
      status="404"
      title="Страница не найдена"
      subTitle="Похоже, вы перешли по неверной ссылке."
      extra={
        <Button type="primary">
          <Link to="/">На главную</Link>
        </Button>
      }
    />
  )
}

