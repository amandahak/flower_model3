variable "resource_group_location" {
  type        = string
  default     = "swedencentral"
  description = "Location of the resource group."
}

variable "identifier" {
  type        = string
  description = <<-HEREDOC
    A unique identifier that will identify you from other students in the course. It can also be the group 
    project's identifier, but this would also mean that you need to handle state. This is difficult without using
    a centralized tool such as Terraform Cloud or GitLab CI/CD to do the apply for you. It is recommended that
    each student uses their own identifier and deployes their own infrastructure in their own resource group.
    HEREDOC
}

variable "course_short_name" {
  type        = string
  default     = "olearn"
  description = "The short name of the course. This is used in the naming of the resources."

}

variable "default_tags" {
  type        = map(string)
  description = "Default tags that are applied to all resources."
  default = {
    Owner       = "KAMK"
    Environment = "student"
    CostCenter  = "1020"
    Course      = "TT00CB27-3002"
  }
}

variable "frontend_image" {
  type        = string
  description = "The image to use for the frontend container (The Draw Hello Streamlit UI)."
  default     = "cropeolearn.azurecr.io/flowerui:1.0"
}

variable "backend_image" {
  type        = string
  description = "The image to use for the backend container (The Predict Hello Fast API)"
  default     = "cropeolearn.azurecr.io/flowerpredict:1.0"

}

variable "modeller_image" {
  type        = string
  description = "The image to use for the modeller container (The Scikit Learn Modeller)"
  default     = "cropeolearn.azurecr.io/modeller:1.0"
}

variable "use_azure_credential" {
  type    = bool
  default = false
}
